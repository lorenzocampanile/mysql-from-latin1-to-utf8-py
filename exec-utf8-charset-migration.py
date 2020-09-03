# -*- coding: UTF-8 -*-

import argparse
import MySQLdb


class Table():

    RAW_INFORMATION_SCHEMA_QUERY = '''
        SELECT TABLE_NAME, TABLE_COLLATION
        FROM   TABLES
        WHERE  TABLE_SCHEMA = %s
    '''

    def __init__(self):
        self.name = ''
        self.collation = ''

    @staticmethod
    def from_raw_res(res):
        '''Returns an instance of Table from a raw MySQL query result.'''
        table = Table()

        table.name = res[0]
        table.collation = res[1]

        return table


class TableColumn():

    RAW_INFORMATION_SCHEMA_QUERY = '''
        SELECT COLUMN_NAME, COLLATION_NAME, COLUMN_TYPE, DATA_TYPE,
                CHARACTER_OCTET_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
        FROM   COLUMNS
        WHERE  TABLE_SCHEMA    = %s
                AND TABLE_Name      = %s
                AND COLLATION_NAME IN(%s,%s,%s)
                AND COLLATION_NAME IS NOT NULL
    '''

    def __init__(self):
        self.name = ''
        self.collation_name = ''
        self.type = ''
        self.data_type = ''
        self.octet_length = ''
        self.is_nullable = ''
        self.default = ''

    @staticmethod
    def from_raw_res(res):
        '''Returns an instance of Column from a raw MySQL query result.'''
        tcolumn = TableColumn()

        tcolumn.name = res[0]
        tcolumn.collation_name = res[1]
        tcolumn.type = res[2]
        tcolumn.data_type = res[3]
        tcolumn.octet_length = res[4]
        tcolumn.is_nullable = res[5] == 'YES'
        tcolumn.default = res[6]

        return tcolumn


class MySQLCharsetConverter():

    def __init__(self, args):
        # Pretend mode -- show only SQL command without executing them
        self.pretend_mode = args.pretend_mode

        # Should SET and ENUM columns be processed?
        self.process_enums = args.process_enums

        # The collation you want to convert the overall database to
        self.default_collation = args.default_collation

        # Convert column collations and table defaults using this mapping
        # latin1_swedish_ci is included since that's the MySQL default.
        #
        # TODO: edit this if needed
        self.collation_map = {
            'latin1_bin': 'utf8_bin',
            'latin1_general_ci': 'utf8_unicode_ci',
            'latin1_swedish_ci': 'utf8_unicode_ci'
        }

        # Database connection parameters
        self.db_host = args.dbhost
        self.db_name = args.dbname
        self.db_user = args.dbuser
        self.db_pass = args.dbpass

        # Properties for store the queries to apply on a table
        self.intermediate_query_changes = []
        self.final_query_changes = []

        # Databases cursors
        self.info_db_cursor = None
        self.target_db_cursor = None

    def convert_to_utf8(self):
        '''Run the database conversion to UTF-8.'''

        # Open a connection to the information_schema database
        info_db = MySQLdb.connect(passwd=self.db_pass, db="information_schema")
        self.info_db_cursor = info_db.cursor()

        # Open a second connection to the target (to be converted) database
        target_db = MySQLdb.connect(passwd=self.db_pass, db=self.db_name)
        self.target_db_cursor = target_db.cursor()

        #
        # TODO: FULLTEXT Indexes
        #
        # You may need to drop FULLTEXT indexes before the conversion -- execute the drop here.
        #
        # If so, you should restore the FULLTEXT index after the conversion -- search for 'TODO'
        # later in this script.
        #

        # Get all the tables in the specified database
        self.info_db_cursor.execute(Table.RAW_INFORMATION_SCHEMA_QUERY,
                                    (self.db_name, ))

        # Convert each database table to UTF-8
        for res in self.info_db_cursor.fetchall():

            # Clean the SQL commands for the table
            self.intermediate_query_changes = []
            self.final_query_changes = []

            # Collect SQL code for converting each table to UTF-8
            table = Table.from_raw_res(res)
            self._collect_table_to_utf8_sql(table)

            # Run queries for converting the database
            if self.intermediate_query_changes:
                intermediate_sql_cmd = 'ALTER TABLE `%(dbname)s`.`%(tablename)s`\n' % {
                    'dbname': self.db_name,
                    'tablename': table.name,
                } + ',\n'.join(self.intermediate_query_changes)
                final_sql_cmd = 'ALTER TABLE `%(dbname)s`.`%(tablename)s`\n' % {
                    'dbname': self.db_name,
                    'tablename': table.name,
                } + ',\n'.join(self.final_query_changes)

                # Show the SQL
                print('*** SQL that would be executed: %s' % intermediate_sql_cmd)
                print('*** SQL that would be executed: %s' % final_sql_cmd)

                # If pretend mode is off, run the SQL
                if not self.pretend_mode:
                    self.target_db_cursor.execute(intermediate_sql_cmd)
                    self.target_db_cursor.execute(final_sql_cmd)

        #
        # TODO: Restore FULLTEXT indexes here
        #

        # Set the database default collate to UTF-8.
        # Show command and, if pretend mode is off, run the SQL
        set_default_collation_cmd = 'ALTER DATABASE `%(dbname)s` COLLATE %(defaultcollation)s' % {
            'dbname': self.db_name,
            'defaultcollation': self.default_collation,
        }
        print('*** SQL that would be executed: %s' % set_default_collation_cmd)
        if not self.pretend_mode:
            self.info_db_cursor.execute(set_default_collation_cmd)

        # Commit all modifications, rollback it there are any errors
        try:
            target_db.commit()
            print('\n\n------------ MYSQL CONVERSION TO UTF-8 DONE -------------\n\n')
        except:
            target_db.rollback()

        # Close all the database connections
        target_db.close()
        info_db.close()


    def _collect_table_to_utf8_sql(self, table):
        '''Collects SQL commands for converting a database table to UTF-8.'''

        # Find all columns whose collation is of one of $mapstring's source types
        self.info_db_cursor.execute(TableColumn.RAW_INFORMATION_SCHEMA_QUERY,
                                    (self.db_name, table.name, ) + tuple(self.collation_map.keys()))

        for res in self.info_db_cursor.fetchall():
            tcolumn = TableColumn.from_raw_res(res)

            # If this column doesn't use one of the collations we want to handle, skip it
            if tcolumn.collation_name not in self.collation_map:
                continue

            self._collect_columns_to_utf8_sql(tcolumn)

        if table.collation in self.collation_map:
            self.final_query_changes.append('DEFAULT COLLATE %s' % self.collation_map.get(table.collation))

    def _collect_columns_to_utf8_sql(self, tcolumn):
        '''Collects SQL commands for converting a database column to UTF-8.'''

        # Collect useful query parts
        target_collation = self.collation_map[tcolumn.collation_name]
        q_tcol_null = '' if tcolumn.is_nullable else 'NOT NULL'
        q_tcol_default = '' if tcolumn.default is None else "DEFAULT '%s'" % tcolumn.default

        # Determine the target temporary BINARY type
        tmp_data_type = self._get_tmp_col_binary_type(tcolumn)

        # ENUM data-type isn't using a temporary BINARY type -- just convert its column type directly
        if tmp_data_type == 'SKIP' and self.process_enums:
            self.final_query_changes.append('MODIFY `%(colname)s` %(coltype)s COLLATE %(default_collation)s %(q_tcol_null)s %(q_tcol_default)s' % {
                'colname': tcolumn.name,
                'coltype': tcolumn.type,
                'default_collation': self.default_collation,
                'q_tcol_null': q_tcol_null,
                'q_tcol_default': q_tcol_default,
            })

            # Any data types marked as SKIP were already handled
            return

        # Change the column definition to the new type
        tmp_col_type = tcolumn.type.replace(tcolumn.data_type, tmp_data_type)

        # Convert the column to the temporary BINARY cousin
        self.intermediate_query_changes.append('MODIFY `%(colname)s` %(tmp_col_type)s %(colnull)s' % {
            'colname': tcolumn.name,
            'tmp_col_type': tmp_col_type,
            'colnull': q_tcol_null,
        })

        # Convert it back to the original type with the correct collation
        self.final_query_changes.append('MODIFY `%(colname)s` %(coltype)s COLLATE %(targetcollation)s %(colnull)s %(coldefault)s' % {
            'colname': tcolumn.name,
            'coltype': tcolumn.type,
            'targetcollation': target_collation,
            'colnull': q_tcol_null,
            'coldefault': q_tcol_default,
        })

    def _get_tmp_col_binary_type(self, tcolumn):
        '''Get the temporary BINARY type for the column.'''
        up_data_type = tcolumn.data_type.upper()

        # Map of "Normal text data types" --> "Binary data type"
        DATA_TYPE_BINARY_MAP = {
            'CHAR': 'BINARY',
            'VARCHAR': 'VARBINARY',
            'TINYTEXT': 'TINYBLOB',
            'TEXT': 'BLOB',
            'MEDIUMTEXT': 'MEDIUMBLOB',
            'LONGTEXT': 'LONGBLOB',
            'SET': 'SKIP',
            'ENUM': 'SKIP',
        }

        # Define the correspondent binary data type for the column
        binary_data_type = DATA_TYPE_BINARY_MAP.get(up_data_type, '')

        # If the data type is not handled raise an error
        if not binary_data_type:
            raise ValueError('Unkwnown datatype "%s" of column "%s"' %
                             (tcolumn.data_type, tcolumn.name))

        return binary_data_type


def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--pretend-mode', action='store_true', required=False)
    argparser.add_argument('--process-enums', action='store_true', required=False)
    argparser.add_argument('--default-collation', default='utf8_unicode_ci', required=False)

    argparser.add_argument('--dbhost', required=True)
    argparser.add_argument('--dbname', required=True)
    argparser.add_argument('--dbuser', required=True)
    argparser.add_argument('--dbpass', required=True)

    args = argparser.parse_args()

    charset_converter = MySQLCharsetConverter(args)
    charset_converter.convert_to_utf8()


if __name__ == '__main__':
    main()