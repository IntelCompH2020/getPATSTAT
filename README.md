# getPATSTAT

Download latest version of PATSTAT using REST API access. ZIP files are donwloaded, uncompressed, and saved target directory.

Usage:

1. Install requirements

2. Rename `config.cf.default` as `config.cf`. Edit to include your credentials and destination folder

3. Run script

    $ python getPATSTAT.py
    
If you prefer, an alternative configuration file can be specified with the `-c` flag. You can also modify the destination directory in the command line `python getPATSTAT.py -p <dest_path>``

