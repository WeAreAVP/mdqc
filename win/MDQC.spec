# -*- mode: python -*-
a = Analysis(['MDQC.py'],
             pathex=['c:\\Users\\Xohotech\\Desktop\\projects\\MDQC'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
for d in a.datas:
    if 'pyconfig' in d[0]: 
        a.datas.remove(d)
        break
a.datas += [('assets\\avpreserve-2.png', 'assets\\avpreserve-2.png', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='MDQC.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='assets\\avpreserve-1.ico')
app = BUNDLE(exe, name=os.path.join('dist', 'MDQC.exe.app'))