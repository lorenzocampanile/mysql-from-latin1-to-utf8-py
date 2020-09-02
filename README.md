# MySQL, from Latin1-encoded to UTF-8 encoded
Convert a Latin1 encoded database to a UTF-8 encoded database.

This script is intended for Latin1 encoded databases that have data saved in UTF-8.

A **great** explanation of how convert a database from Latin1 to Unicode can be found here: [article from Nic Jansma](https://nicj.net/mysql-converting-an-incorrect-latin1-column-to-utf8/).

This script is just the Python version of the [Nic Jansma script in PHP](https://github.com/nicjansma/mysql-convert-latin1-to-utf8).

**A big thank you to [Nic Jansma](https://nicj.net/about/)**

---

## Summary

Sometimes it happens, after years, that we realize that a company database is using Latin1 encoding.

Although the business software uses this database as if it were UTF-8, (almost) everything worked and we didn't notice anything until a customer pointed out a flaw due to a WHERE clause.

We look into the problem and what?... the encoding is Latin1.

**What to do?**

The problems and difficulties are brilliantly explained and solved in Nic Jansma's article.

Anyway if you are lazy: make a backup of your database, import it on a test machine and run this script to see if it solves your problem.

---

## How to use

Simply download and run the script:
```bash
cd /tmp/
wget https://github.com/lorenzocampanile/mysql-from-latin1-to-utf8-py/archive/master.zip
unzip master.zip
cd mysql-from-latin1-to-utf8-py-master/
python exec-utf8-charset-migration.py --dbhost=localhost --dbname=mydatabase --dbuser=myuser --dbpass=mypass --process-enums
```

If you just want to see the SQL statements without executing them, run the script in the pretend mode:
```bash
python exec-utf8-charset-migration.py --dbhost=localhost --dbname=mydatabase --dbuser=myuser --dbpass=mypass --process-enums --pretend-mode
```

---

## Why this script if there is already the Nic Jansma one?

The company I work for had some hundreds of VPS with this problem, install PHP on all the machines just for run the Nic Jansma's script isn't desirable.
My boss preferred a Python version (**rightfully**) so here we are.
