# -*- mode: python -*-
a = Analysis(['.\\security_test.py'],
             pathex=['C:\\Users\\Student\\Documents\\notes\\github\\Scriptable_Game'],
             hiddenimports=[],
             hookspath=None,
             excludes=[sys,os],
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='security_test.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
