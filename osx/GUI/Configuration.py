# -*- coding: UTF-8 -*-
'''
Created on May 14, 2014

@author: Furqan Wasi <furqan@avpreserve.com>
'''
import os, datetime, sys, platform, base64



class Configuration(object):
    def __init__(self):

        # Constructor
        if os.name == 'posix':
            self.OsType = 'linux'
        elif os.name == 'nt':
            self.OsType = 'Windows'
        elif os.name == 'os2':
            self.OsType = 'check'


        self.application_name = 'Metadata Quality Control'
        self.application_version = '0.3'

        self.user_home_path = os.path.expanduser('~')

        if self.OsType == 'Windows':
            self.base_path = str(os.getcwd())+str(os.sep)
            self.assets_path = r''+(os.path.join(self.base_path, 'assets'+str(os.sep)))

            try:
                self.avpreserve_img = os.path.join(sys._MEIPASS, 'assets' + (str(os.sep)) +'avpreserve.png')
            except:
                pass

        else:
            self.base_path = str(os.getcwd())+str(os.sep)
            self.assets_path = r''+(os.path.join(self.base_path, 'assets'+str(os.sep)))
            self.avpreserve_img = r''+(os.path.join(self.assets_path) + 'avpreserve.png')

        self.logo_sign_small = 'logo_sign_small.png'


    def getImagesPath(self):return str(self.assets_path)

    def getAvpreserve_img(self):return self.avpreserve_img

    def getBasePath(self):return str(self.base_path)

    def getApplicationVersion(self):return str(self.application_version)
    def getConfig_file_path(self):
        return self.config_file_path

    def EncodeInfo(self, string_to_be_encoded):
        string_to_be_encoded = str(string_to_be_encoded).strip()
        return base64.b16encode(base64.b16encode(string_to_be_encoded))


    def getLogoSignSmall(self):
        if self.getOsType() == 'Windows':
            try:
                return os.path.join(sys._MEIPASS, 'assets' + (str(os.sep)) + str(self.logo_sign_small))
            except:
                pass
        else:
            os.path.join(self.assets_path)
            return os.path.join(self.assets_path, str(self.logo_sign_small))

    def getOsType(self):return str(self.OsType)

    def getApplicationName(self): return str(self.application_name)



    def getUserHomePath(self): return str(os.path.expanduser('~'))

    def getDebugFilePath(self):return str(self.log_file_path)


    def getWindowsInformation(self):
        """
        Gets Detail information of Windows
        @return: tuple Windows Information
        """
        WindowsInformation = {}
        try:
            major,  minor,  build,  platformType,  servicePack = sys.getwindowsversion()
            WindowsInformation['major'] = major
            WindowsInformation['minor'] = minor
            WindowsInformation['build'] = build

            WindowsInformation['platformType'] = platformType
            WindowsInformation['servicePack'] = servicePack
            windowDetailedName = platform.platform()
            WindowsInformation['platform'] = windowDetailedName
            windowDetailedName = str(windowDetailedName).split('-')

            if windowDetailedName[0] is not  None and (str(windowDetailedName[0]) == 'Windows' or str(windowDetailedName[0]) == 'windows'):
                WindowsInformation['isWindows'] =True
            else:
                WindowsInformation['isWindows'] =False

            if windowDetailedName[1] is not None and (str(windowDetailedName[1]) != ''):
                WindowsInformation['WindowsType'] =str(windowDetailedName[1])
            else:
                WindowsInformation['WindowsType'] =None

            WindowsInformation['ProcessorInfo'] = platform.processor()

            try:
                os.environ["PROGRAMFILES(X86)"]
                bits = 64
            except:
                bits = 32
                pass

            WindowsInformation['bitType'] = "Win{0}".format(bits)
        except:

            pass
        return WindowsInformation



    def CleanStringForBreaks(self,StringToBeCleaned):
        """
        @param StringToBeCleaned:

        @return:
        """
        CleanString = StringToBeCleaned.strip()
        try:
            CleanString = CleanString.replace('\r\n', '')
            CleanString = CleanString.replace('\n', '')
            CleanString = CleanString.replace('\r', '')
        except:
            pass

        return CleanString