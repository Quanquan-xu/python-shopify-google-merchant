# -*- coding: utf-8 -*-
import paramiko
import os
import re
import time
from config.configuration import init_remote_files_downloader, init_files_manager
from remote_download.prepare_data import PrepareData


class RemoteDownloader:
    def __init__(self):
        self.date_str = time.strftime("%Y%m%d", time.localtime())
        self.root_path = os.path.dirname(__file__)
        self.local_dir = None

    def download_remote_files(self, shop_name_abbr="ST"):
        remote_downloads = init_remote_files_downloader(shop_name_abbr)
        files_dir_manager = init_files_manager(self.root_path, shop_name_abbr, self.date_str)
        self.local_dir = files_dir_manager.get("DownloadFilesDir")
        try:
            for remote_downloader in remote_downloads:
                self._download_remote_files(remote_downloader, shop_name_abbr)
            PrepareData.run(shop_name_abbr, self.date_str)
        except Exception as e:
            print(e)
            return False
        else:
            return True

    def _download_remote_files(self, remote_downloader, shop_name):
        prefix, downloader, file_filter = remote_downloader
        local_dir = self.local_dir
        # save_file_name = "{}_{}_{}.csv".format(shop_name, prefix, self.date_str).lower()
        save_file_name = "{}_{}_{}_".format(shop_name, prefix, self.date_str).lower()

        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
            self._remote_download(downloader, file_filter, save_file_name)
        else:
            all_files = os.listdir(local_dir)
            if save_file_name not in all_files:
                self._remote_download(downloader, file_filter, save_file_name)

    def _remote_download(self, downloader, file_filter, file_name):
        hostname = downloader.get("hostname")
        username = downloader.get("username")
        password = downloader.get("password")
        port = downloader.get("port")
        remote_dir = downloader.get("remote_dir")
        local_dir = self.local_dir

        try:
            t = paramiko.Transport((hostname, port))
            t.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(t)
            files = sftp.listdir(remote_dir)
            for f in files:
                if re.search(r'{}'.format(file_filter), f):
                    print("$" * 30)
                    print('Downloading file:', os.path.join(remote_dir, f))
                    save_file_name = "{}{}".format(file_name, f)
                    # save_file_name = file_name
                    # sftp.get(os.path.join(remote_dir, f), os.path.join(local_dir, save_file_name))
                    sftp.get(os.path.join(remote_dir, f), os.path.join(local_dir, save_file_name))
                    print('Download {} file success'.format(save_file_name))
            t.close()
        except Exception as e:
            print(e)
