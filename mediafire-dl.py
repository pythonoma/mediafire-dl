#!/usr/bin/python

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import sys
import os
import errno
import time

chunk_size = 1024 # 32KB
os_path_separator = os.path.sep



def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


class MediafireDownloader:
    dl_file_name = ''
    dl_file_full_path = ''
    dl_total_file_size = 0
    dl_existing_file_size = 0

    dl_page_url = ''
    dl_file_url = ''

    def __init__(self):
        pass

    def get_subfolders_from_folder(self, folder_key, parent):
        api_call_link = "http://mediafire.com/api/1.5/folder/get_content.php?folder_key=" + folder_key + \
                        "&content_type=folders&chunk_size=1000&response_format=json"
        resp_json = requests.get(api_call_link).json()
        subfolders_in_folder = resp_json['response']['folder_content']['folders']

        if subfolders_in_folder == []:
            # No subfolders >> don't request it again
            return False

        for subfolder in subfolders_in_folder:
            subfolder_name = subfolder['name']
            subfolder_parent = parent + subfolder_name + os_path_separator
            subfolder_key = subfolder['folderkey']

            print('----------------------------')
            print('Downloading folder: ' + subfolder_parent)
            self.download_folder(subfolder_key, subfolder_parent)


    def download_files_in_folder(self, folder_key, parent):
        api_call_link = "http://mediafire.com/api/1.5/folder/get_content.php?folder_key=" + folder_key \
                        + "&content_type=files&chunk_size=1000&response_format=json"
        resp_json = requests.get(api_call_link).json()
        files_in_folder = resp_json['response']['folder_content']['files']

        for file in files_in_folder:
            file_page_url = file['links']['normal_download']
            self.download_file(file_page_url, parent)


    def download_folder(self, folder_key, parent):
        # Get files in current folder
        cur_folder_files = self.download_files_in_folder(folder_key, parent)

        # Get files in subfolders
        self.get_subfolders_from_folder(folder_key, parent)




    def download(self, mediafire_link):
        mediafire_folder_key = "mediafire.com/folder/"
        folder_slug_start = mediafire_link.find(mediafire_folder_key) + len(mediafire_folder_key)
        if folder_slug_start < 0:
            self.download_file(mediafire_link)
        else:
            hash_pos = mediafire_link.rfind('#') + 1
            if hash_pos > 0:
                # Folder is after #
                folder_key = mediafire_link[hash_pos:]
            else:
		folder_slug_end = mediafire_link.find('/', folder_slug_start)
		if folder_slug_end < 0:
			folder_slug_end = len(mediafire_link)
                folder_key = mediafire_link[folder_slug_start:folder_slug_end]
            self.download_folder(folder_key, '')


    def download_file1111(self, mediafire_file_link, parent, file_name=''):
        print('Downloading ' + mediafire_file_link)


    #@staticmethod
    def download_file(self, mediafire_file_link, parent, file_name=''):
        cwd = os.getcwd()
        self.dl_page_url = mediafire_file_link
        print('----------------')
        print('Getting link from ' + self.dl_page_url)

        # Get download element
        r_download_page = requests.get(self.dl_page_url)
        soup_download_page = BeautifulSoup(r_download_page.text, 'lxml')
        download_link_element = soup_download_page.select_one('.download_link')
        download_link_element_str = str(download_link_element)

        # Get download link from download element
        link_start = download_link_element_str.find('"http://') +1
        link_end = download_link_element_str.find('";', link_start)
        self.dl_file_url = download_link_element_str[link_start:link_end]

        # Get file_name & file_size from HTTP head request
        header_request = requests.head(self.dl_file_url)
        self.dl_total_file_size = int(header_request.headers['Content-Length'])
        if file_name != '':
            self.dl_file_name = file_name
        else:
            cd = header_request.headers['content-disposition']
            file_name_key = 'filename="'
            fn_start = cd.find(file_name_key) + len(file_name_key)
            fn_end = cd.find('"', fn_start)
            self.dl_file_name = cd[fn_start:fn_end]
        ss = os.path.join(cwd, parent)
        make_sure_path_exists(ss)
        self.dl_file_full_path = os.path.join(cwd, parent, self.dl_file_name)

        #print('download link: ' + self.dl_file_url)
        #print('[' + str(self.dl_total_file_size) + ']' + 'File: ' + self.dl_file_name)

        # If file already exist, resume. Otherwise create new file
        if os.path.exists(self.dl_file_full_path):
            output_file = open(self.dl_file_full_path, 'ab')
            self.dl_existing_file_size = int(os.path.getsize(self.dl_file_full_path))
        else:
            output_file = open(self.dl_file_full_path, 'wb')

        if self.dl_existing_file_size == self.dl_total_file_size:
            print('File "' + str(os.path.join(parent, self.dl_file_name)) + '" Already downloaded.')
            print('-------------------------')
            time.sleep(2)
        else:
            print('Resuming "' + self.dl_file_full_path + '".')
            # Add header to resume download
            headers = {'Range': 'bytes=%s-' % self.dl_existing_file_size}
            r = requests.get(self.dl_file_url, headers=headers, stream=True)
            #try:
            # for chunk in tqdm(r.iter_content(32*1024), total=self.dl_total_file_size, \
            #                   unit='KB', unit_scale=True):
            pbar = tqdm(total=self.dl_total_file_size, initial=self.dl_existing_file_size,
                        unit='B', unit_scale=True)
            for chunk in r.iter_content(chunk_size):
                output_file.write(chunk)
                pbar.update(chunk_size)

            output_file.close()
            pbar.close()
            print('Finished Downloading "' + self.dl_file_full_path + '".')
            print('-------------------------')
            # except:
            #     output_file.close()


def main():
    #print(sys.argv)
    if len(sys.argv) < 2:
        print('Use: mediafire.py mediafre_link_1 mediafire_link_2')
        exit()

    mf = MediafireDownloader()

    for mediafire_link in sys.argv[1:]:
         mf.download(mediafire_link)
    #mf.download(mf_folder_url)

if __name__ == "__main__":
    main()

