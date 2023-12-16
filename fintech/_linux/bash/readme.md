
# Bash Manual Page
I read the bash manual from cover to cover. I found practical examples and use cases for just about
everything it has to offer and will be presenting this to you in this video. This is not just a review
of the manual, but a practical tour guide that will help you go from zero to Bash-Master!

# Intro


# Basic Concepts

## REPL
REPL stands for: Read, Evaluate, Print, Loop.
It's the fundamentals of how a command line shell works. Back in the early days of computing, there
were punch cards that told the computer what to do. It would read what you put on the punch card,
evaluate the request, print results you could see on a TV screen. Loop just says do that over and
over again.

Summary: So what bash is going to do is read input from you, evaluate what you want it to do, print
the results to the screen, then repeat this process until program termination (or you turn your
computer off).

Bash is also known as an "interpreted language" from a computer programming standpoint.
For more information on the differences between language types, checkout my video on
&#35;ProgrammingTheory in the description.

You can use Bash to write scripts and even entire full applications!

## Command Structures
Let's review commands in a shell environment:

    executable arg1 "argument two" 'arg 3'

The first word you typically see in command line work is the command itself. It is the program you
are trying to run. Things that follow after that are called "arguments".
Arguments are a way to argue with the command to get it to do something different or provide it some
kind of input in order to achieve a certain output.

Arguments come in all shapes and sizes. You have bare arguments in bash, or things that are implied
to be part of the same string because they contain no operator or special characters that tell bash
to do something different. Yes, that's right, bash itself will try to parse objects out before passing
them to the command you specified.

If we observe the above example, you'll notice the first argument doesn't have any quotes around it,
yet the other two do. This is because the first argument contains no special characters that make bash
think its any different than a string; it shall be treated as such.

If you look at the other two arguments, you'll notice they have different types of quotes around them.
The double quotes are parseable. This means you can insert variables, subshells and other sundries
into these strings and bash can still try to parse them out.

The third argument indicates what's called a "literal string". A literal string is to be taken literally.
In other words, nothing is parsed and the string is taken at face-value.

Bash has a limit of 1024 placeholders you can use as arguments to another program. Keep that in mind
if you encounter a situation where more than a thousand results could end up on the command line.
The error message you'll get for this is "argument list too long".

## Basic Commands
Let's start with some basic commands. You will use these quite frequently in your personal and
professional settings:

    echo 

The `echo` command is used to output anything you want. It's helpful for seeing the contents of
variables, outputting statement results and telling you what's going on in a script.


    ls

The `ls` command will list files and folders in the computer. This is one of the commands you need
to browse files.


    cat

The `cat` command is short for "concatenate". This program will print the contents of any file you
give on the argument list.

For more breakdowns on common Linux commands, checkout my video on Linux commands you'll want to know.
\#LinuxCommands. This video will stay focused on the fundamentals of bash itself and not all the
commands available in Linux.

## Basic Uses
The command line terminal is like our way of talking to the computer and getting it to do things.


# Scripts


