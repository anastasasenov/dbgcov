#!/usr/bin/python3

"""
Coverage module routines

# lldb a.out -o 'command script import dbgcov.py'

"""

import lldb
import os
import sys
import time


def help_string():
    """Help message."""
    return """    Provides platform independent module coverage info.

    Syntax: cvg [ -b <breakpoint> ]  - initial breakpoint, default 'main'
                [ -f <output file> ] - report file, default 'stdout'
                [ -l <level> ]       - logging level, default 0
                [ -m <module name> ] - module pattern, default 'a.out'
                [ -p <path substr ]  - path pattern, default ''
                [ -t <seconds> ]     - report period, default 10 seconds"""


class CCoverage:
    """Coverage module class."""

    err_no_error = 0
    err_lldb_cmd_failed = 1
    err_lldb_parser_opts_failed = 2
    err_invalid_module = 3
    err_no_source = 4

    type_method = 0
    type_all = 1
    
    level_no_log = 0
    level_log_opts = 1
    level_log_command_output = 2
    level_log_module_files = 3
    level_trace_breakpoints = 4

    buffer_size = 1234

    opt_b = "-b"
    opt_f = "-f"
    opt_l = "-l"
    opt_m = "-m"
    opt_p = "-p"
    opt_t = "-t"
    
    def __init__(self, dbg, cmd, res):
        """Constructor."""
        self.m_dbg = dbg
        self.m_cmd = cmd
        self.m_res = res
        self.m_err_code = CCoverage.err_no_error
        self.m_breakpoint = 'main'
        self.m_level = CCoverage.level_no_log
        self.m_module_pattern = '/tmp/a.out'
        self.m_path_pattern = ''
        self.m_file = ""
        self.m_period = 10
        self.m_fH = None
        self.m_tm = 0

    def __del__(self):
        """Destructor."""
        if None != self.m_fH:
            self.m_fH.close()

    def do(self):
        """Do coverage sequence."""
        if self.parse_opts():
            self.output("Custom command coverage ( cvg ) ...")
            if self.m_level >= CCoverage.level_log_opts:
                self.log_opts()
            self.m_err_code = self.coverage_proc()
            if CCoverage.err_no_error == self.m_err_code:
                self.output("Done.")
            elif CCoverage.err_no_source == self.m_err_code:
                self.output( "ERROR: There is no acceptable source." )
            elif CCoverage.err_invalid_module == self.m_err_code:
                self.output('ERROR: Invalid module.')
                self.output('Please choose one, here is the list of modules:')
                target = self.m_dbg.GetSelectedTarget()
                for m in target.module_iter():
                    self.output( str(m) )
        else:
            self.output('ERROR: Invalid options.')

    def parse_opts(self):
        """Parse command line options."""
        if "help" == str(self.m_cmd).strip():
            self.m_res.AppendMessage(help_string())
            self.m_err_code = CCoverage.err_lldb_parser_opts_failed
            return False
        aOpt = str(self.m_cmd).split()
        for i in range(0, len(aOpt), 2):
            if ( i + 1 ) >= len(aOpt):
                break
            if aOpt[ i ] == CCoverage.opt_b:
                self.m_breakpoint = aOpt[ i + 1 ]
            elif aOpt[ i ] == CCoverage.opt_f:
                try:
                    self.m_file = aOpt[ i + 1 ]
                    self.m_fH = open(self.m_file, "w")
                except:
                    self.m_fH = None
                    self.m_file = ''
            elif aOpt[ i ] == CCoverage.opt_l:
                if aOpt[ i + 1 ].isdigit():
                    self.m_level = int( aOpt[ i + 1] )
            elif aOpt[ i ] == CCoverage.opt_m:
                self.m_module_pattern = aOpt[ i + 1 ]
            elif aOpt[ i ] == CCoverage.opt_p:
                self.m_path_pattern = aOpt[ i + 1 ]
            elif aOpt[ i ] == CCoverage.opt_t:
                if aOpt[ i + 1 ].isdigit():
                    self.m_period = int( aOpt[ i + 1] )
        return True

    def log_opts(self):
        """Logging options."""
        self.output("    initial breakpoint: " + self.m_breakpoint )
        self.output("    report file: " + ("<stdout>" if len(self.m_file) == 0 else self.m_file) )
        self.output("    logging level: " + str(self.m_level) )
        self.output("    module pattern: " + self.m_module_pattern )
        self.output("    path pattern: " + self.m_path_pattern )
        self.output("    report period: " + str(self.m_period) + " seconds" )
       
    def run_lldb_cmd(self, command_line):
        """Run lldb command."""
        cmd_interpreter = self.m_dbg.GetCommandInterpreter()
        ret_obj = lldb.SBCommandReturnObject()
        cmd_interpreter.HandleCommand(command_line, ret_obj)
        if ret_obj.Succeeded():
            if self.m_level >= CCoverage.level_log_command_output:
                return (command_line + " : " + str(ret_obj.GetOutput()))
            else:
                return (command_line + " : done")
        else:
            self.m_err_code = CCoverage.err_lldb_cmd_failed
            return str(ret_obj)

    def output_lldb_proc(self, process):
        """Processing stdout/stderr."""
        p_stdout = process.GetSTDOUT(CCoverage.buffer_size)
        if p_stdout:
            print("\n%s" % (process_stdout))
            while p_stdout:
                p_stdout = process.GetSTDOUT(CCoverage.buffer_size)
                print(p_stdout)
        p_stderr = process.GetSTDERR(CCoverage.buffer_size)
        if p_stderr:
            print("\n%s" % (p_stderr))
            while p_stderr:
                p_stderr = process.GetSTDERR(CCoverage.buffer_size)
                print(p_stderr)

    def listener_lldb(self, process):
        """Processing lldb listener."""
        listener = self.m_dbg.GetListener()
        isDone = False
        while not isDone:
            event = lldb.SBEvent()
            if listener.WaitForEvent(0, event):
                if lldb.SBProcess.EventIsProcessEvent(event):
                    state = lldb.SBProcess.GetStateFromEvent(event)
                    isDone = True
            else:
                isDone = True
            self.output_lldb_proc(process)

    def output(self, txt):
        """Coverage output messages."""
        msg = "[ " + time.strftime("%H:%M:%S", time.localtime()) + " ] cvg: " + txt        
        if None == self.m_fH:
            print( msg )
        else:
            saved_stdout = sys.stdout
            sys.stdout = self.m_fH
            print( msg )
            sys.stdout = saved_stdout
            self.m_fH.flush()

    def out_cvg(self, visited, marked, forced = False):
        """Output info about coverage."""
        if 0 == marked:
            marked = 1
        if not forced:
            if (int(time.time()) - self.m_tm) < self.m_period:
                return
        txt = 'Coverage '
        txt = txt + str(round(100.0 * ( visited / marked ), 3)) + " %"
        txt = txt + " ( " + str( visited ) + " / " + str(marked) + " )"
        self.output( txt )
        self.m_tm = int(time.time())

    def find_lines( self, strFilename ):
        """Find valid lines in file."""
        aLine = [ ]
        f = None
        try:
            f = open(strFilename, 'r')
            nLine = 0
            for i in f.readlines():
                nLine = nLine + 1
                if len(i.strip()) > 1:
                    aLine.append( nLine )
        except:
            pass
        if None != f:
            f.close()
        return aLine

    def count_bp(self, target):
        """Count breakpoints."""
        return target.num_breakpoints
        
    def marked_by_file(self, target, module):
        """Count code by address."""
        for compile_unit in module.compile_units:
            if compile_unit.file:
                file_str = str(compile_unit.file)
                if len(self.m_path_pattern) > 0:
                    if file_str.find( self.m_path_pattern ) < 0:
                        continue
                for i in self.find_lines( file_str ):
                    self.out_cvg( 0, self.count_bp(target) )
                    bp = target.BreakpointCreateByLocation(compile_unit.file, i)
                    if bp.num_locations == 0:
                        target.BreakpointDelete( bp.id )
                    else:
                        bp.SetOneShot(True)
                if self.m_level >= CCoverage.level_trace_breakpoints:
                    self.output( "Added: " + file_str )
        if self.m_level >= CCoverage.level_trace_breakpoints:
            self.output( 'Marked places: ' )
            self.output( self.run_lldb_cmd( "br list" ) )
        self.out_cvg( 0, self.count_bp(target), True )

    def count_visited_bp(self, marked_count, target):
        """Count visited points."""
        target = self.m_dbg.GetSelectedTarget()
        process = target.GetProcess()
        self.output('Running ...')
        while not self.is_finished( process ):
            self.output_lldb_proc(process)
            self.listener_lldb(process)
            self.out_cvg(marked_count - self.count_bp(target), marked_count)
            process.Continue()
        return ( marked_count - self.count_bp(target) )

    def delete_all_bp(self, target):
        """Delete all breakpoints."""
        while self.count_bp( target ):
            for bp in target.breakpoint_iter():
                target.BreakpointDelete( bp.id )
                break

    def coverage_proc(self):
        """Coverage processing."""
        self.output( self.run_lldb_cmd( "b " + self.m_breakpoint ) )
        self.output( self.run_lldb_cmd( "run" ) )
        target = self.m_dbg.GetSelectedTarget()
        self.delete_all_bp( target )
        module = None
        for m in target.module_iter():
            if str( m ).find( self.m_module_pattern ) >= 0:
                module = m
        if None == module:
            return CCoverage.err_invalid_module
        self.output('Found module: ' + str(module))
        self.output('Counting ...')
        self.marked_by_file(target, module)
        marked_count = self.count_bp( target )
        if 0 == marked_count:
            return CCoverage.err_no_source
        self.output( self.run_lldb_cmd( "kill" ) )
        self.output( self.run_lldb_cmd( "run" ) )
        visited = self.count_visited_bp(marked_count, target)
        if visited != marked_count and self.m_level >= CCoverage.level_trace_breakpoints:
            self.output( 'Unvisited places: ' )
            self.output( self.run_lldb_cmd( "br list" ) )
        self.out_cvg( visited, marked_count, True )

    def is_finished(self, process):
        """Check if program is finished."""
        thread = process.GetSelectedThread()
        frame = thread.GetFrameAtIndex(0)
        if len(str(frame).strip()) == 0:
            return True
        return False

def __lldb_init_module(debugger, dict):
    """Load lldb custom commands."""
    debugger.HandleCommand('command script add -f dbgcov.dbgcov cvg')
    print('The "cvg" command has been installed, type "cvg help" for detailed help.')


def dbgcov(debugger, command, result, internal_dict):
    """Process dbgcov custom command."""
    oCvg = CCoverage(debugger, command, result)
    oCvg.do()

# end of file

