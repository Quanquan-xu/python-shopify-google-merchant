# -*- coding: utf-8 -*-
from remote_download.remote_downloader import RemoteDownloader
from remote_download.price_split_helper import PriceSplitHelper
from remote_download.shopify_price_updater import ShopifyPriceUpdate
from config.configuration import init_files_manager
import pandas
import os
import shutil
import time
import datetime


class AutoUpdatePrice:
    def __init__(self, shop_name_abbr, gap_price=2, compare=">", plus_limit=None, minus_limit=-8, query_code=None):
        self.shop_name = shop_name_abbr
        self.gap_price = gap_price
        self.compare = compare
        self.plus_limit = plus_limit
        self.minus_limit = minus_limit
        self.query_code = query_code
        self.download_count = 1
        self.exception_count = 0
        self.remote_downloader = RemoteDownloader()
        self.split_helper = PriceSplitHelper()
        self.update_helper = None
        self.deadline_end_time = datetime.datetime.today() + datetime.timedelta(hours=20)
        self.date_str = time.strftime("%Y%m%d", time.localtime())
        self.root_path = os.path.dirname(__file__)
        files_manager = init_files_manager(self.root_path, shop_name_abbr, self.date_str)
        self.price_files_dir = files_manager.get("PriceFilesDir")
        self.download_file_dir = files_manager.get("DownloadFilesDir")
        self.price_file_name = files_manager.get("PriceSave")

    def _check_remote_download_status(self, download_status):
        if download_status:
            mix_price_list = self.split_helper.split_price(self.shop_name, self.gap_price, self.compare,
                                                           self.plus_limit, self.minus_limit, self.query_code)
            if mix_price_list.empty:
                raise TypeError("There is something about splitting price data. Please check site value")
            else:
                return mix_price_list
        else:
            self.download_count = self.download_count + 1
            if self.download_count <= 5:
                print("Try to re-download remote files after {}-time fail".format(self.download_count))
                self._init_files()
            else:
                raise TypeError("Remote-Download-Files fails after trying 5 times")

    def _check_running_expiration_date(self):
        running_time = datetime.datetime.today()
        if running_time > self.deadline_end_time:
            return False
            # raise TimeoutError("Daily Update Time Out")
        else:
            return True

    def _init_files(self):
        download_status = self.remote_downloader.download_remote_files(self.shop_name)
        price_update_list = self._check_remote_download_status(download_status)
        return price_update_list

    def _update_price(self):
        price_list_file = os.path.join(self.price_files_dir, self.price_file_name)
        if os.path.exists(price_list_file):
            price_update_list = pandas.read_csv(price_list_file, delimiter="\t")
        else:
            price_update_list = self._init_files()
        print("Update Data Size: {}".format(price_update_list.shape[0]))
        update_helper = ShopifyPriceUpdate(self.shop_name)
        update_helper.deadline_end_time = self.deadline_end_time
        update_helper.product_variant_price_update_by_pandas_data(price_update_list)

    def _escape_unexpected_exception(self):
        try:
            self._update_price()
        except Exception as e:
            self.exception_count = self.exception_count + 1
            if self.exception_count <= 7:
                print("Restart A New Google Merchant Client - {}".format(e))
                self.auto_update_price()
            else:
                raise TypeError("Remote-Download-Files fails after trying 20 times")

    def auto_update_price(self, drop_files=False):
        time_status = self._check_running_expiration_date()
        if time_status:
            self._escape_unexpected_exception()
        else:
            print("Daily Update Time Out")
        if drop_files:
            shutil.rmtree(self.price_files_dir, ignore_errors=True)
            shutil.rmtree(self.download_file_dir, ignore_errors=True)
