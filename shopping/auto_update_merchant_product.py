# -*- coding: utf-8 -*-
from shopping.google_merchant_helper import GoogleMerchantHelper


class AutoUpdateMerchantProduct:
    def __init__(self, shop_name_abbr, start_page=1, end_page=None):
        self.shop_name = shop_name_abbr
        self.start_page = start_page
        self.end_page = end_page
        self.exception_count = 0

    def _update_merchant_product(self):
        google_merchant_helper = GoogleMerchantHelper(self.shop_name)
        google_merchant_helper.resubmit_product_to_merchant_by_all_pages(self.start_page, self.end_page)

    def _escape_unexpected_exception(self):
        try:
            self._update_merchant_product()
        except Exception as e:
            self.exception_count = self.exception_count + 1
            if self.exception_count <= 20:
                print("Restart A New Google Merchant Client - {}".format(e))
                self.run()
            else:
                raise TypeError("Restart A New Google Merchant Client fails after trying 20 times")

    def run(self):
        self._escape_unexpected_exception()
