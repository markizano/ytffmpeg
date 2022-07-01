
When I was working in WebDev land, I came across a pattern here and I wanted to show that to you.
However, first, I need to explain some concepts that will help illustrate the pattern in a way that
will make this picture clear by the end of this video.

Let's go over the following concepts:
- URL's - What are they and how to read them.
- CLI Commands - How to run programs from that black terminal of text?
- Functions - How to run code within code?


# URL's
When you click on those blue links that lead you to some web page, that's called a Universal Resource
Locator. You'll also see URI, which means Universal Resource Identifier. Semantically, there's not
much of difference, albeit, there might be a few nuances in some very specific contexts as to why
this matters.

Let's break down what this means:


    [protocol] :// [username] : [password] @ [hostname] : [port] [path-to-executable] ? [argument=value] & [argument=value]


In a URL, you have the following:
- Protocol
- UserName
- Password
- Hostname
- Port
- Path to Program
- Query-String Arguments

Protocol: Most times, this is HTTP or HTTPS. (HTTP=Hypertext Transfer Protocol/Secure).
It can be just about anything you want it to be, though in your own context. You can reference files
on your local filesystem in the browser by using "file://" protocol.

UserName/Password: These are access credentials in order to gain authentication (if required) to access
the resources. With everything on the Internet being open to the world, in most cases, by default,
it's sometimes important to ensure you know who's accessing said resource. Take care with HTTP Basic
Digest authentication because credentials are sent in Plaintext. For more details, please see the linked
video about the HTTP Protocol.

Hostname: The IP address or named address (e.g. DNS Name) of the target machine or endpoint that will
be used to access the program in question. The DNS Name will be translated to an IP address and your
computer will be directed to this machine to complete the remainder of the request.

Port: The Port is kinda like the TV Channel. At least, that's how I always thought about it. For the
most part 80 is HTTP and 443 is HTTPS. You can do what you want with the port as well. Any app can serve
any content from just about any port. Some apps have a port hardcoded into them, which is bad practice.
Don't hardcode ports. Always allow them to be configured by the user somehow and just use a default
if not defined.

Path: The path to the program or executable to run. Web servers have gotten smarter and allow you to
access a "smart resource" via something like "/myapp" instead of "/myapp/index.php", for example.
In any case, the path to the executable is where you access your resource on the remote.

Query-String Arguments: Querystring arguments are user input that sends additional data to the application
behind the server. These are ways for the user to say different things to the app to get it to do
different things and return various outputs.


# Commands
When you run commands, they have a similar pattern. Let's review the anatomy of a command line program
run in your terminal:

    [path] [argument=value] [argument=value]

Path: This is where the program is run. In your local system, you have a $PATH or %PATH% variable.
This defines the list of places to look for programs runnable by your computer. When the computer
finds the program, it tries to open and execute it in some fashion. This can be a script or a binary
executable.

Command-Line Arguments: These are a set of inputs from the user that tells the program to do something
different or process the data provided by the user.

I just want to call out a few things about commands run from the terminal as well: The user is already
authenticated to the local machine. So username and password are not required here. The hostname is not
required since the command is to be run on the local machine. The shape might be becoming more clear
at this point, but we'll tie it all together after the next point.

# Functions

When calling functions, there's a way the computer must "navigate" to find the function to call as
well. Let's break this down:

    [packageName].[className].[functionName]( [argument=value], [argument=value] )

Package Name: This is a way for the computer to "navigate" the filesystem to find the particular file
containing the code to run. It's an encapsulation mechanism for the containing file for the code. You
can think of this to be the "hostname" in previous examples to help the computer find the bundle of
code that needs to be run.

Class Name: This is the encapsulation layer for a bundle of code. Classes are a way to define functions
that all relate to each other in a way that contains everything those set of functions need in a single
context. Classes may have multiple functions and use cases. You can think of a class as a computer
on the network in the URL example or the local machine in the CLI example.

Function Name: This is the name of the function to call. It's very much like the executable in the
previous two examples. You invoke the function by calling it somewhere else in your program.

Function Arguments: This is where user-data or outside information enters the function for it to
process into results. This can be user data, results from other functions or other places where data
may be formatted or processed to return a value via this function.


# Tying It All Together
To bring this all together, I think of each of these to be the same virtual "shape" in my mind:
- Protocol: Is it a file? Is it a web address? Is it code to call? Is it a function to run?
- UserName/Password: Credentials and access to the target resource.
- Hostname: From where should this be invoked?
- Path: Location of the file or function to run.
- Arguments: User-provided input to help us get a different outcome from the target function to call.


By this argument: A URL, a command, and a function are all the same thing, just implemented in a
different way with a few details off here and there to tweak their use case.


I thought this was fascinating. If you agree, hit that like button on your way out.
Subscribe if you like this IT kind of stuff and want to learn more practical ways to implement all
this random tutorial stuff on the Interwebz!


