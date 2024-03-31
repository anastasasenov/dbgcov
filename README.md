# dbgcov
LLDB python scripts to extend coverage commands for debugging

Yet another coverage tool that is very simple and easy to use. The script implemented line coverage using lldb one-shot breakpoints. The tool registers a custom command as LLDB coverage extension. 


## Importing the commands
In LLDB, execute:

```lldb
command script import <path>/dbgcov.py
```

## Commands

- cvg help - Prints help
- cvg -m a.out - Runs coverage on given module 


## Batch

- lldb a.out -b -o 'command script import dbgcov.py' -o 'cvg -m a.out'

```lldb
[ 13:05:04 ] cvg: Custom command coverage ( cvg ) ...
[ 13:05:12 ] cvg: Found module: (x86_64) /home/default/projects/demo/a.out
...
[ 13:05:12 ] cvg: Counting ...
[ 13:05:12 ] cvg: Coverage 0.0 % ( 0 / 1 )
[ 13:05:18 ] cvg: Coverage 0.0 % ( 0 / 14530 )
...
[ 13:05:23 ] cvg: Running ...
[ 13:05:44 ] cvg: Coverage 0.599 % ( 87 / 14530 )
[ 13:06:24 ] cvg: Coverage 3.152 % ( 458 / 14530 )
```


## Inspired by

gcov - coverage testing tool


## Troubleshooting

If something does not work, try running these commands:

```shell
# apt install python3-lldb

