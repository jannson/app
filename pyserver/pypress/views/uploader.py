# -*- coding: utf-8 -*-

import os
import re
import json
import base64
import random
import urllib
import datetime
from io import BytesIO
from cStringIO import StringIO
from six import text_type, PY2

from pypress.extensions.routing import route

_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')

class WrapFileObj(object):
    def __init__(self, field):
        self.stream = StringIO(field["body"])
        #self.stream.write(field["body"])
        self.stream.seek(0, 0)
        self.filename = field["filename"]

    def save(self, path):
        with open(path, "wb") as fw:
            fw.write(self.stream.getvalue())

def secure_filename(filename):
        r"""Pass it a filename and it will return a secure version of it.  This
        filename can then safely be stored on a regular file system and passed
        to :func:`os.path.join`.  The filename returned is an ASCII only string
        for maximum portability.

        On windows system the function also makes sure that the file is not
        named after one of the special device files.

        >>> secure_filename("My cool movie.mov")
        'My_cool_movie.mov'
        >>> secure_filename("../../../etc/passwd")
        'etc_passwd'
        >>> secure_filename(u'i contain cool \xfcml\xe4uts.txt')
        'i_contain_cool_umlauts.txt'

        The function might return an empty filename.  It's your responsibility
        to ensure that the filename is unique and that you generate random
        filename if the function returned an empty one.

        .. versionadded:: 0.5

        :param filename: the filename to secure
     """
        if isinstance(filename, text_type):
            from unicodedata import normalize
            filename = normalize('NFKD', filename).encode('ascii', 'ignore')
            if not PY2:
                filename = filename.decode('ascii')
        for sep in os.path.sep, os.path.altsep:
            if sep:
                filename = filename.replace(sep, ' ')
        filename = str(_filename_ascii_strip_re.sub('', '_'.join(
                    filename.split()))).strip('._')

        # on nt a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename.  In
        # this case we prepend an underline
        if os.name == 'nt' and filename and \
        filename.split('.')[0].upper() in _windows_device_files:
            filename = '_' + filename

        return filename

class Uploader:

    stateMap = [  # 上传状态映射表，国际化用户需考虑此处数据的国际化
        "SUCCESS",  # 上传成功标记，在UEditor中内不可改变，否则flash判断会出错
        "文件大小超出 upload_max_filesize 限制",
        "文件大小超出 MAX_FILE_SIZE 限制",
        "文件未被完整上传",
        "没有文件被上传",
        "上传文件为空",
    ]

    stateError = {
        "ERROR_TMP_FILE": u"临时文件错误",
        "ERROR_TMP_FILE_NOT_FOUND": u"找不到临时文件",
        "ERROR_SIZE_EXCEED": u"文件大小超出网站限制",
        "ERROR_TYPE_NOT_ALLOWED": u"文件类型不允许",
        "ERROR_CREATE_DIR": u"目录创建失败",
        "ERROR_DIR_NOT_WRITEABLE": u"目录没有写权限",
        "ERROR_FILE_MOVE": u"文件保存时出错",
        "ERROR_FILE_NOT_FOUND": u"找不到上传文件",
        "ERROR_WRITE_CONTENT": u"写入文件内容错误",
        "ERROR_UNKNOWN": u"未知错误",
        "ERROR_DEAD_LINK": u"链接不可用",
        "ERROR_HTTP_LINK": u"链接不是http链接",
        "ERROR_HTTP_CONTENTTYPE": u"链接contentType不正确"
    }

    def __init__(self, fileobj, config, static_folder, _type=None):
        """
        :param fileobj: FileStorage, Base64Encode Data or Image URL
        :param config: 配置信息
        :param static_folder: 文件保存的目录
        :param _type: 上传动作的类型，base64，remote，其它
        """
        self.fileobj = fileobj
        self.config = config
        self.static_folder = static_folder
        self._type = _type
        if _type == 'base64':
            self.upBase64()
        elif _type == 'remote':
            self.saveRemote()
        else:
            self.upFile()

    def upBase64(self):
        # 处理base64编码的图片上传
        img = base64.b64decode(self.fileobj)
        self.oriName = self.config['oriName']
        self.fileSize = len(img)
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()

        # 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateError('ERROR_SIZE_EXCEED')
            return

        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(self.filePath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.stateInfo = self.getStateError('ERROR_CREATE_DIR')
                return
        elif not os.access(dirname, os.W_OK):
            self.stateInfo = self.getStateError('ERROR_DIR_NOT_WRITEABLE')
            return

        try:
            with open(self.filePath, 'wb') as fp:
                fp.write(img)
            self.stateInfo = self.stateMap[0]
        except:
            self.stateInfo = self.getStateError('ERROR_FILE_MOVE')
            return

    def upFile(self):
        # 上传文件的主处理方法
        self.oriName = self.fileobj.filename

        # 获取文件大小
        #self.fileobj.stream.seek(0, 2)
        self.fileSize = self.fileobj.stream.tell()
        self.fileobj.stream.seek(0, 0)

        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()

        # 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateError('ERROR_SIZE_EXCEED')
            return

        # 检查是否不允许的文件格式
        if not self.checkType():
            self.stateInfo = self.getStateError('ERROR_TYPE_NOT_ALLOWED')
            return

        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(self.filePath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.stateInfo = self.getStateError('ERROR_CREATE_DIR')
                return
        elif not os.access(dirname, os.W_OK):
            self.stateInfo = self.getStateError('ERROR_DIR_NOT_WRITEABLE')
            return

        # 保存文件
        try:
            self.fileobj.save(self.filePath)
            self.stateInfo = self.stateMap[0]
        except:
            self.stateInfo = self.getStateError('ERROR_FILE_MOVE')
            return

    def saveRemote(self):
        _file = urllib.urlopen(self.fileobj)
        self.oriName = self.config['oriName']
        self.fileSize = 0
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()

        # 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateError('ERROR_SIZE_EXCEED')
            return

        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(self.filePath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.stateInfo = self.getStateError('ERROR_CREATE_DIR')
                return
        elif not os.access(dirname, os.W_OK):
            self.stateInfo = self.getStateError('ERROR_DIR_NOT_WRITEABLE')
            return

        try:
            with open(self.filePath, 'wb') as fp:
                fp.write(_file.read())
            self.stateInfo = self.stateMap[0]
        except:
            self.stateInfo = self.getStateError('ERROR_FILE_MOVE')
            return

    def getStateError(self, error):
        # 上传错误检查
        return self.stateError.get(error, 'ERROR_UNKNOWN')

    def checkSize(self):
        # 文件大小检测
        return self.fileSize <= self.config['maxSize']

    def checkType(self):
        # 文件类型检测
        return self.fileType.lower() in self.config['allowFiles']

    def getFilePath(self):
        # 获取文件完整路径
        rootPath = self.static_folder
        filePath = ''
        for path in self.fullName.split('/'):
            filePath = os.path.join(filePath, path)
        return os.path.join(rootPath, filePath)

    def getFileExt(self):
        # 获取文件扩展名
        return ('.%s' % self.oriName.split('.')[-1]).lower()

    def getFullName(self):
        # 重命名文件
        now = datetime.datetime.now()
        _time = now.strftime('%H%M%S')

        # 替换日期事件
        _format = self.config['pathFormat']
        _format = _format.replace('{yyyy}', str(now.year))
        _format = _format.replace('{mm}', str(now.month))
        _format = _format.replace('{dd}', str(now.day))
        _format = _format.replace('{hh}', str(now.hour))
        _format = _format.replace('{ii}', str(now.minute))
        _format = _format.replace('{ss}', str(now.second))
        _format = _format.replace('{ss}', str(now.second))
        _format = _format.replace('{time}', _time)

        # 过滤文件名的非法自负,并替换文件名
        _format = _format.replace('{filename}',
                                  secure_filename(self.oriName))

        # 替换随机字符串
        rand_re = r'\{rand\:(\d*)\}'
        _pattern = re.compile(rand_re, flags=re.I)
        _match = _pattern.search(_format)
        if _match is not None:
            n = int(_match.groups()[0])
            _format = _pattern.sub(str(random.randrange(10**(n-1), 10**n)), _format)

        _ext = self.getFileExt()
        return '%s%s' % (_format, _ext)

    def getFileInfo(self):
        # 获取当前上传成功文件的各项信息
        filename = re.sub(r'^/', '', self.fullName)
        return {
            'state': self.stateInfo,
            'url': "/static/uploads/"+filename,
            'title': self.oriName,
            'original': self.oriName,
            'type': self.fileType,
            'size': self.fileSize,
        }
