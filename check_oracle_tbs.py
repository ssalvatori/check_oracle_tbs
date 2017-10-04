#!/usr/bin/python

import cx_Oracle
import re
import pprint
import os
import argparse
import sys

def main(dbhost, port, user, password, service_name, excluded_tables=None, warning_level=85, critical_level=95, check_autoextensible=True):

    print "warning: %s critical: %s" % (warning_level, critical_level)

    try:
        dsnStr = cx_Oracle.makedsn(host=dbhost, port=port, service_name=service_name)
        connection = cx_Oracle.connect(user=user, password=password, dsn=dsnStr)

        cursor = connection.cursor()
        cursor.execute("""
		SELECT
			NVL(b.tablespace_name,nvl(a.tablespace_name,'UNKOWN')) name,
			((kbytes_alloc-nvl(kbytes_free,0))/kbytes_alloc)*100 pct_used,
			NVL(kbytes_free/1024,0) free,
			autoextensible
		FROM
			(SELECT
				SUM(bytes)/1024 Kbytes_free,
				max(bytes)/1024 largest,
				tablespace_name
			FROM
				sys.dba_free_space
			GROUP BY
				tablespace_name
			) a,
			(SELECT SUM(bytes)/1024 Kbytes_alloc,
				tablespace_name
			FROM
				sys.dba_data_files
			GROUP BY
				tablespace_name
			) b,
			(SELECT
				tablespace_name,
				autoextensible
			FROM
				sys.dba_data_files
			GROUP BY
				tablespace_name,
				autoextensible
			HAVING
				autoextensible='YES'
			) c
			WHERE
				a.tablespace_name (+) =  b.tablespace_name
			AND
				c.tablespace_name (+) = b.tablespace_name
		""")

        if (excluded_tables):
            regexp_exclude = re.compile('(%s)'%excluded_tables)

        remaining = 0

        for result in cursor:
            '''
                result[0] tablespace_name
                result[1] pct_used
                result[2] free
                result[3] autoextensible
            '''

            if not regexp_exclude.match(result[0]):
                remaining += float(result[2])
                
                if float(result[1]) >= critical_level:
                    print "%s CRITICAL %.2f" % (result[0], result[1])
                    continue

                if float(result[1]) >= warning_level:
                    print "%s WARNING %.2f" % (result[0], result[1])
                    continue

        print "Remaining free space = %.2fMb" % remaining

    except Exception as e:
        print e

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Check tablespace size')

    parser.add_argument('--db_host', required=True, dest='db_host' ,metavar='db_host', type=str, help="Oracle host")
    parser.add_argument('--db_port', required=True, dest='db_port' ,metavar='db_port', type=str, help="Oracle port")
    parser.add_argument('--db_user', required=True, dest='db_user', metavar='db_user', type=str, help="Oracle user")
    parser.add_argument('--db_password', required=True, dest='db_password', metavar='db_password', type=str, help="Oracle password")

    parser.add_argument('--db_service_name', required=True, dest='db_service_name', metavar='db_service_name', type=str, help="Oracle service_name")
    parser.add_argument('-e', metavar='exclusion', dest='exclusion', type=str, help="regex for tablespace exclusion (example: -e='UNDOTBS[0-9]')")
    parser.add_argument('-w', metavar='warning', dest='warning_level', default=85.0, type=float, help="usage percent for warning")
    parser.add_argument('-c', metavar='critical', dest='critical_level', default=95.0, type=float, help="usage percent for critical alert")
    parser.add_argument('-wauto', metavar='wauto', dest='wauto', type=bool, help="usage percent for warning on autoextensible tablespaces")

    args = parser.parse_args()

    main(args.db_host, args.db_port, args.db_user, args.db_password,
        args.db_service_name, args.exclusion,
        args.warning_level, args.critical_level, args.wauto)
