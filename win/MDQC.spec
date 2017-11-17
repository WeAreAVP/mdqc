# -*- mode: python -*-

block_cipher = None


a = Analysis(['MDQC.py'],
             pathex=['tools', 'E:\\Projects\\mdqc\\win'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          Tree('E:\\Projects\\mdqc\\win\\tools', prefix='tools\\'),
          a.zipfiles,
          a.datas,
          name='MDQC',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='assets\\avpreserve-1.ico')
