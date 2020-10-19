# -*- coding: utf-8 -*-
import time
import sqlite3
import pandas
import pyisbn


class Databases:

    def __init__(self, name="myDatabase.db"):
        self.database_name = name
        self.database_status = False
        self.is_auto_add_created_date = False
        self.created_date_pattern = "%Y-%m-%d %H:%M:%S"
        self._conn = None
        self._cursor = None
        self._table_name = None
        self._default_column_name = None
        self._default_column_value = None
        self._default_constrain = "PRIMARY KEY"
        self._constrain_list = ["PRIMARY KEY", 'UNIQUE', "NOT NULL"]
        self._columns_name_list = []
        self.item_value_list = []

    def connect_databases(self):
        try:
            conn = sqlite3.connect(self.database_name)
        except Exception as e:
            print(e)
        else:
            self._conn = conn
            self._cursor = conn.cursor()
    
    def close_connection(self):
        self._conn.close()

    def add_table_constrain(self, column_name, constrain):
        sql_string = "ALTER TABLE {} ADD COLUMN {} {}".format(self._table_name, column_name, constrain)
        # sql_string = "ALTER TABLE {} ALTER COLUMN {} SET {}".format(self._table_name, column_name, constrain)
        print(sql_string)
        self._execute_sql(sql_string)

    def create_table_by_columns_constrains(self, table_name, constrains, suffix=None):
        self._table_name = table_name
        self.connect_databases()
        if isinstance(constrains, dict):
            self._columns_name_list = list(constrains.keys())
            sql_string = "CREATE TABLE  IF NOT EXISTS {} (\n".format(table_name)
            for key, value in constrains.items():
                sql_string = sql_string + key + " " + value + ",\n"
            if suffix:
                if isinstance(suffix, list):
                    suffix = ",\n".join(suffix)
                sql_string = sql_string + suffix + ",\n"
            sql_string = sql_string[:-2] + "\n)"
            print(sql_string)
            self._execute_sql(sql_string)
        else:
            pass

    def set_delegate_table_name(self, table_name, columns_name_list=None):
        self._table_name = table_name
        if columns_name_list:
            self._columns_name_list = columns_name_list
        self.database_status = True
        self.connect_databases()

    def get_database_tables_name(self):
        self.connect_databases()
        sql_string = "SELECT name FROM sqlite_master WHERE type='table'"
        if self._execute_sql(sql_string):
            response = self._cursor.fetchall()
            response = [list(name)[0] for name in response]
        else:
            response = []
        self.close_connection()
        return response

    def update_data(self, column_name_list, column_value_list, where_name=None, where_value=None):
        if not where_name or not where_value:
            where_name = self._default_column_name
            where_value = self._default_column_value
        if not isinstance(column_name_list, list):
            column_name_list = [column_name_list]
            column_value_list = [column_value_list]
        if "created_date" not in column_name_list and self.is_auto_add_created_date:
            localtime = time.strftime(self.created_date_pattern, time.localtime())
            column_name_list.append("created_date")
            column_value_list.append(localtime)
        column_data_list = ["{} = \'{}\'".format(column_name_list[index], column_value_list[index]) for index in range(len(column_name_list))]
        update_info = ", ".join(column_data_list)
        sql_string = "UPDATE {} SET {} WHERE {} = \'{}\'".format(self._table_name, update_info, where_name, where_value)
        self._execute_sql(sql_string)

    def query_table_column_data(self, column_name=None):
        if not column_name:
            column_name_list = ["*"]
        else:
            column_name_list = column_name if isinstance(column_name, list) \
                else [column_name] if isinstance(column_name, str) else ["*"]
        query_table_column_info = ','.join(column_name_list)
        sql_string = "SELECT {} FROM {}".format(query_table_column_info, self._table_name)
        if self._execute_sql(sql_string):
            response = self._cursor.fetchall()
            return response
        else:
            return None

    def query_data(self, column_value=None, column_name=None):

        if not column_value and not column_name:
            sql_string = "SELECT * FROM {}".format(self._table_name)
        else:
            if not column_name:
                column_name = self._default_column_name
            else:
                self._default_column_name = column_name
            self._default_column_value = column_value
            sql_string = "SELECT * FROM {} WHERE {} = \'{}\'".format(self._table_name, column_name, column_value)

        if self._execute_sql(sql_string):
            response = self._cursor.fetchall()
            return response
        else:
            return None

    def add_data(self, columns_value_list, columns_name_list=None):
        if self.database_status:
            if isinstance(columns_value_list, list):
                if self.is_auto_add_created_date:
                    localtime = time.strftime(self.created_date_pattern, time.localtime())
                    columns_value_list.append(localtime)
                else:
                    if not columns_name_list:
                        if len(columns_value_list) != len(self._columns_name_list):
                            raise TypeError('The number of items value is not equal to the number of items name')
                        sql_string = "INSERT INTO {} VALUES{}".format(self._table_name, tuple(columns_value_list))
                    else:
                        if len(columns_value_list) != len(columns_name_list):
                            raise TypeError('The number of items value is not equal to the number of items name')
                        sql_string = "INSERT INTO {} {} VALUES{}".format(self._table_name,
                                                                         tuple(columns_name_list),
                                                                         tuple(columns_value_list))
                    # print(sql_string)
                    self._execute_sql(sql_string)
            else:
                raise TypeError('item_value_list must be a list')
        else:
            raise TypeError("The database is not initialised! You firstly need to invoke init_databases function")

    def delete_table_column(self, column_value, column_name=None):
        if not column_name:
            column_name = self._default_column_name
        sql_string = "DELETE FROM {} WHERE {} = \'{}\'".format(self._table_name, column_name, column_value)
        self._execute_sql(sql_string)

    def drop_table(self):
        sql_string = "DROP TABLE IF EXISTS {}".format(self._table_name)
        self._execute_sql(sql_string)
        
    def _execute_sql(self, sql_string):
        try:
            self._cursor.execute(sql_string)
        except Exception as e:
                print(sql_string)
                print("ERROR : {}".format(e))
                return False
        else:
            self._conn.commit()
            return True

    def execute_sql(self, sql_string):
        self.connect_databases()
        try:
            self._cursor.execute(sql_string)
        except Exception as e:
                print("ERROR : {}".format(e))
                self.close_connection()
                return None
        else:
            self._conn.commit()
            response = self._cursor.fetchall()
            self.close_connection()
            return response

    def query_table_info(self):
        sql_string = "SELECT * FROM {}".format(self._table_name)
        if self._execute_sql(sql_string):
            response = self._cursor.fetchall()
            return response
        else:
            return None

    def init_databases(self, table_name, columns_name_list=None):
        if columns_name_list and isinstance(columns_name_list, list):
            self._default_column_name = columns_name_list[0]
            if "created_date" not in columns_name_list and self.is_auto_add_created_date:
                columns_name_list.append("created_date")
            else:
                self.is_auto_add_created_date = False
            self._columns_name_list = columns_name_list
            sql_string = "CREATE TABLE  IF NOT EXISTS {} {}".format(table_name, tuple(columns_name_list))
            self.connect_databases()
            self._table_name = table_name
            self._execute_sql(sql_string)
            self.database_status = True
        else:
            raise TypeError("Columns can't satisfy the requirements when CREATE TABLE ")


if __name__ == '__main__':
    import os
    import re
    abstract_dir = os.path.dirname(__file__)
    relative_dir = '/download_files/ST'
    target_dir = abstract_dir + relative_dir
    price_file_filter = "db$"
    reference_file_filter = "20200204\.csv$"

    listOfFiles = os.listdir(target_dir)
    price_columns = ["isbn10", "basic_price", "condition"]
    reference_columns = ["site", "product_id",	"variant_id", "old_price",
                         "quantity", "isbn10", "condition", "download_time"]
    price_list = pandas.DataFrame(columns=price_columns)
    reference = pandas.DataFrame(columns=reference_columns)
    print(listOfFiles)
    for f in listOfFiles:
        if re.search(r'{}'.format(price_file_filter), f):
            database = Databases(os.path.join(target_dir, f))
            tables = database.get_database_tables_name()
            if len(tables) == 1:
                table = tables[0]
                database.set_delegate_table_name(table)
                results = database.query_table_info()
                data = pandas.DataFrame(results, columns=price_columns)
                data['condition'] = table.split("_")[1]
                price_list = price_list.append(data)
        elif re.search(r'{}'.format(reference_file_filter), f):
            data = pandas.read_csv(os.path.join(target_dir, f), sep='\t')
            reference = reference.append(data)
        else:
            pass
    merged_data = pandas.merge(reference, price_list, how='left', on=['isbn10', 'condition'])
    merged_data['basic_price'] = merged_data['basic_price'].apply(lambda x: 0 if x != x else x)
    merged_data['basic_price'] = merged_data['basic_price'].apply(lambda x: 0 if x == 'None' else x)
    print(merged_data.shape)
    # price_list = merged_data[["site", "product_id", "variant_id", "basic_price"]]
    # price_list_file_name = "st_price_20200313.csv"
    #
    # reference = merged_data[["product_id", "variant_id", "old_price", "quantity"]]
    # reference_file_name = "st_reference_20200313.csv"
    #
    # price_list.to_csv(os.path.join(target_dir, price_list_file_name), index=False, sep='\t')
    # reference.to_csv(os.path.join(target_dir, reference_file_name), index=False, sep='\t')
    # listOfFiles = os.listdir(target_dir)
    # for f in listOfFiles:
    #     if f not in [price_list_file_name, reference_file_name]:
    #         os.remove(os.path.join(target_dir, f))