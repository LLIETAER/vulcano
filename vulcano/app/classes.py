# -* coding: utf-8 *-
"""
:py:mod:`vulcano.app.classes`
-----------------------------
Vulcano APP Classes
"""
# System imports
from __future__ import print_function
import sys
import os
from difflib import SequenceMatcher

# Third-party imports
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import FuzzyCompleter
from prompt_toolkit.lexers import PygmentsLexer

# Local imports
from vulcano.exceptions import CommandNotFound
from vulcano.command import builtin
from vulcano.command.classes import Magma
from vulcano.command.completer import CommandCompleter
from vulcano.command.parser import inline_parser, split_list_by_arg
from .lexer import create_lexer, MonokaiTheme


__all__ = ["VulcanoApp"]


def rq_is_for_repl(app):
    def _func():
        return not app.request_is_for_args
    return _func


def did_you_mean(command, possible_commands):
    suggested_command = None
    ratio = 0
    for possible_command in possible_commands:
        possible_ratio = SequenceMatcher(None, command, possible_command).ratio()
        if possible_ratio > ratio:
            ratio = possible_ratio
            suggested_command = possible_command
    return suggested_command


class VulcanoApp(object):
    """VulcanoApp"""
    __instances__ = {}

    def __new__(cls, app_name='vulcano_default'):
        if app_name in cls.__instances__:
            return cls.__instances__.get(app_name)
        new_app = _VulcanoApp(app_name)
        cls.__instances__[app_name] = new_app
        return new_app


class _VulcanoApp(object):
    """ App is the class choosen for managing the application.

    It has the all the things needed to command/execute/manage commands."""

    def __init__(self, app_name):
        self.app_name = app_name
        self.manager = Magma()  # type: Magma
        self.context = {}  # Type: dict
        self.print_result = True
        self.theme = None
        self.suggestions = None

    @property
    def request_is_for_args(self):
        """ Returns if the request is for running with args or in REPL mode

        :return: Request is to be run with args or not
        :rtype: bool
        """
        return len(sys.argv) >= 2

    def command(self, *args, **kwargs):
        """ Register a command under current Vulcano instance

        For more options take a look at `vulcano.command.classes.CommandManager.command`
        """
        return self.manager.command(*args, **kwargs)

    def module(self, module):
        """ Register a module under current Vulcano instance

        :param module: Module could be a string or a module object
        """
        return self.manager.module(module)

    def run(self, prompt=u'>> ', theme=MonokaiTheme, print_result=True, history_file=None, suggestions=did_you_mean):
        """ Start the application

        It will run the application in Args or REPL mode, depending on the
        parameters sent.

        :param theme: Theme to use for this application, NOTE: only used for the REPL.
        :param bool print_result: If True, results from functions will be printed.
        """
        self.theme = theme
        self.suggestions = suggestions
        self.print_result = print_result
        self._prepare_builtins()
        if self.request_is_for_args:
            self._exec_from_args()
        else:
            self._exec_from_repl(prompt=prompt, theme=theme, history_file=history_file)

    def _prepare_builtins(self):
        self.manager.register_command(builtin.exit(self), "exit", show_if=rq_is_for_repl(self))
        self.manager.register_command(builtin.help(self), "help")

    def _exec_from_args(self):
        commands = split_list_by_arg(lst=sys.argv[1:], separator="and")
        for command in commands:
            command_list = command.split()
            command_name = command_list[0]
            arguments = " ".join(command_list[1:])
            try:
                arguments = arguments.format(**self.context)
            except KeyError:
                pass
            args, kwargs = inline_parser(arguments)
            try:
                self._execute_command(command_name, *args, **kwargs)
            except CommandNotFound:
                print('Command {} not found'.format(command_name))
                if self.suggestions:
                    possible_command = self.suggestions(command_name, self.manager.command_names)
                    if possible_command:
                        print('Did you mean: "{}"?'.format(possible_command))

    def _exec_from_repl(self, prompt=u'>> ', theme=MonokaiTheme, history_file=None):
        session_extra_options = {}
        if history_file:
            session_extra_options['history'] = FileHistory(os.path.expanduser(str(history_file)))
        self.do_repl = True
        manager_completer = FuzzyCompleter(
            CommandCompleter(self.manager, ignore_case=True)
        )
        lexer = create_lexer(commands=self.manager.command_names)
        session = PromptSession(
            completer=manager_completer,
            lexer=PygmentsLexer(lexer),
            style=theme.pygments_style(),
            **session_extra_options
        )
        while self.do_repl:
            try:
                user_input = u"{}".format(session.prompt(prompt))
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D Pressed. Finish

            try:
                command_list = user_input.split()
                if not command_list:
                    continue
                command = command_list[0]
                arguments = " ".join(command_list[1:])
                try:
                    arguments = arguments.format(**self.context)
                except KeyError:
                    pass
                args, kwargs = inline_parser(arguments)
                self._execute_command(command, *args, **kwargs)
            except CommandNotFound:
                print('Command {} not found'.format(command))
                if self.suggestions:
                    possible_command = self.suggestions(command, self.manager.command_names)
                    if possible_command:
                        print('Did you mean: "{}"?'.format(possible_command))
            except Exception as error:
                print("Error executing: {}. Error: {}".format(command, error))

    def _execute_command(self, command_name, *args, **kwargs):
        self.context["last_result"] = self.manager.run(command_name, *args, **kwargs)
        if self.print_result and self.context["last_result"]:
            print(self.context["last_result"])
        return self.context["last_result"]
