# MySQL, from Latin1-encoded to UTF-8 encoded
Convert a Latin1 encoded database to a UTF-8 encoded database.

This script is intended for Latin1 encoded databases that have data saved in UTF-8.

A **great** explanation of how convert a database from Latin1 to Unicode can be found here: [article from Nic Jasma](https://nicj.net/mysql-converting-an-incorrect-latin1-column-to-utf8/).

This script is just the Python version of the [Nic Jasma script in PHP](https://github.com/nicjansma/mysql-convert-latin1-to-utf8).

---

## Summary

Sometimes it happens, after years, that we realize that a company database is using Latin1 encoding.
Although the business software uses this database as if it were UTF-8 (almost) everything worked and we didn't notice anything until a customer pointed out a flaw due to a WHERE clause.

We look into the problem and what?... the encoding is Latin1.

**What to do?**

The problems and difficulties are brilliantly explained and solved in Nic Jasma's article.

Anyway if you are lazy: make a backup of your database, import it on a test machine and run this script to see if it solves your problem.

---

## Why this script if there is already the Nic Jasma one?

The company I work for had some hundreds of VPS with this problem, install PHP on all the machines just for run the Nic Jasma's script isn't desirable.
My boss preferred a Python version (**rightfully**) so here we are.
