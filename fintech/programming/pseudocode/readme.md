
# Intro

Greetings and welcome to Kizano's FinTech where I take you from Zero to Master in IT and DevOps.

In this video, we'll be covering the basics and fundamentals to programming. This video will be
foundational to a lot of future videos coming out on more specific things, so subscribe if you
want to be notified of when those come out. Here, I teach you about variables, control structures,
types of programming and code. I introduce you to a lot of the theory behind programming.

Generally, the concepts described in this video are applicable to almost any programming language
regardless of which syntax that is used. So this will be useful no matter what language you learn
from here on out.

With that said, you can use the timestamps below if you are in a hurry, but watching all the way
through will ensure that you get the full set of concepts this video has to offer. This is one I'll
shill a bit more and say I'll reference a lot of things from this from more advanced concepts, so
you definitely don't want to miss what's next!

Finally if that light bulb went off in your head about something, let me know by flicking that like
button. Not only does it help the channel but it also helps the search results when others ask
questions that were answered here.

# Fundamentals
Understanding the fundamentals of programming. By the end of this video, you should have a fairly
basic handle on the fundamentals of programming. It might take a watch or two for it to fully sink
in because I did pack a ton of data into this video. However, you'll enjoy using this as a great
springboard for some of my videos coming out on how to program, so subscribe if you want to continue
this journey to become a professional engineer!

Programming is algebraic english!

I found out early on that computers may speak to each other in 1's and 0's, but we have to speak to
them in a way that makes sense to us. Code and programming is our way of translating our thoughts
and commands into structures that a computer can use.

They say computers were created to perform automated tasks that would otherwise take us humans a
long time to complete. Mostly calculations. I'm going to teach you a few things here that might
seem like Majik! But first, we've got to cover the basics.


# Types of Languages or Programming Styles
There are 3 main Types of languages:
- Procedural/Scripting
- Object-oriented
- Functional

## Procedural
Procedural languages are like sequential commands that tell the computer to do things. They involve
little redirection of thought and you can read the code like you can read a book: from start to finish.

Procedural programming is the easiest to pick up, conceptually, but is the most difficult to maintain.

## Object-Oriented
Object Oriented programming is like procedural except it encapsulates functionality in little bubbles
that make it easy to tie instructions together in a re-usable format.
The idea is if you write a piece of functionality for one purpose, you can use that functionality
for another purpose without having to write that code again.

## Functional
Functional languages definitely do involve more math than your typical setup. Functional languages
are based on a set of functions that must balance out. I'll confess here, I still struggle with
Functional languages, but definitely want to ramp up my skills on these!


# Strong vs Weak Typed Languages
I'll also put on a separate set of lenses and say that programming often comes in two distinct flavors
still: Strongly typed and weakly typed.

Strongly typed languages require you to declare the type of data you are storing and just how much
of it. They have a fixed amount of space that is allocated for their function so they can perform
faster than loosely typed languages.

Loosely typed languages are more relaxed about the data type and approach code with more of a "if it
quacks, it must be a duck" style of coding.


# Interpreted vs Compiled Languages
Even still, we can put another set of lenses on to view programming and that is to consider if we
should just write the code and run it, or if we should compile our code to something the computer
can understand before executing the code.

What's the difference?

Compiled languages take the Algebraic English instructions and converts them into what is called
"bytecode" or machine code. This is an intermediary between the raw instructions sent to the hardware
and gibberish if you open it in a text editor. Performing this compilation step ensures a few things
are in place before you go to use the application. Typically, compiled languages are strongly typed,
but this isn't always the case.

Interpreted languages are compiled on-the-fly and can go directly from Algebraic English to machine
code to execution without any steps in between from the programmer's perspective. Languages that
support REPL (Read, Evaluate, Print, Loop) are typically interpreted languages.

Which should you choose?

In an ideal world, you would select the language that best suits your needs and run with that.

In reality, you do what the lead architect says.





# Variables
When programming, most of what you'll be doing is storing data of sorts. Variables are used to store
these values when working with them. Variables, at their core, are just the binary 1's and 0's
computers use to process stuff. However, those 0's and 1's can combine to represent a
universe of information.

You can think of a variable as a box to store data. You might have to define the type of data when
you create it in strongly typed languages. Variables are a way to carry data from one part of your
application to another.

## Primitive Data Types
Let's cover the primary data types:
- Boolean
- Number
-- Float
-- Long
-- Short
- Character

If you're already kinda familiar with programming to some degree, you'll notice I left out "string".
No, not twine, this isn't crochet class! A string is a string of characters. It's a complex type we
will cover in more detail later. For now, just know that a string is not considered a primitive type
by most programming languages.

## Boolean
A boolean is the truest of a binary: It can be true or false. That's it. 0 usually represents false.
1 usually represents true if coerced into numbers. Booleans are useful because they are the fundamental
unit of conditions.

## Number: Int/Long/Short
Numbers come in a few flavors based on the size, sign (+/-) and where/whether there is a decimal.
Integer and Long are two familiar data types that represent whole numbers. There is no decimal place
to represent fractions since the decimal place is fixed at 0. However, this permits you to create
numbers as large as 2^64 and store them in a single variable as a Long itself.

## Number: Float
Numbers that could be fractions or include decimal places are called a "Float" for the "floating decimal
point".

## Number: Signed

## Character
Some languages support the idea of a "character" as a data type. Typically denoted as `char`. There
is a mapping of numbers to letters, numbers and symbols that represent the alphabet. There's also a
few standards for how this mapping is handled. In ASCII, there are 256 characters. In Unicode, there's
upwards of 65534 characters. This data type represents a single character that is the basis of the
`string` data type we will cover in a moment when we do complex data types.


# Complex Data Types
Complex data types are extensions of the primitive data types and build upon the basics when it comes
to describing data in an application.

## String
Strings are basically a string of characters or integers that represent letters on the unicode graph.
Strings are considered complex data types and not native data types since they usually do include
more functionality than primitive data types.

## Array
An array is a list of sorts. It's a way to keep track of a collection of things. You can do fun
things with lists like sorting and filtering. Most programming languages support a variety of
functions against lists natively. You can build more functionality on top of that.

## Object
An object is an object. It represents anything that is a complex data type. I'll be bland here on
purpose because I know the previous definitions are a lot to take in. We will definitely be covering
Objects more in the future as they are a critical component to more complex data structures.
Just know for now that Objects are like the scaffolding required to construct a building as you
continue to construct amazing architectures.   8)

## Operators
In programming, yes, math is involved, but it's very minimal and basic. Most of the mathematical
operations in writing code is mostly associated with the sciences like Physics. Basic operators
are used to combine and assign values to variables that contain data.

Operators include:
- addition +
- subtraction -
- multiplication *
- division /
- power/exponent ^

Basic operators are pretty basic, but I will cover addition here in more detail.

### Addition
The addition (+) operator is great for adding numbers together, as you may have guessed.
However, it's important to note that some languages have a dedicated operation for joining strings
together. Other languages will use the addition operator to join strings together.

Advanced Operators include:
- left bit-shift <<
- right bit-shift >>
- or |
- and &
- exclusive or "xor"

I'll provide resources where you can learn more about these advanced operators. I'll admit, I've
yet to have a practical use-case for them, so I am not as familiar with them as I should be. I
must confess I am not able to explain them accurately, so I won't even try, as that would make a
fool of me.
\#AdvancedOperators in the description.






# Control Structures
Control structures help control how your code will flow.

## If
Just about every programming language will have an `if` control structure. This control structure 
is the start to any condition you will ever write and is usually followed by the condition to test. 
You can use your `and` & `or` operators to assert compound conditions. They will eventually result 
in a boolean and that is the 0's and 1's the computer understands so we can tell it which to do.

## Else
The `else` control structure is an extension of the "if" operator. You cannot have `else` without "if".
The `else` control structure specifies what code to run if the initial condition specified in the "if"
clause is not something we want to execute. The `else` control structure is optional. You do not
require implementing the `else` control structure for every `if` control structure.

## Else-If
The `else-if` control structure varies in syntax across languages, but allows for a way to check for
a series of conditions. The initial `if` control structure says "test this condition", the `else-if`
control structure says "test this condition too" and should be asserted before the final `else`
control structure.

## Loops
No, we're not talking about Fruit Loops, we're talking about coding loops!
Loops are a great way to handle iterations of operations. Instead of copying and pasting code
multiple times in a single project, you can call on loops to iterate over a list or read indefinitely
from a stream to handle data as it passes through your application.

### Loops: While
The first loop type we will cover is the most easiest to understand, which is the `while` loop.
The `while` loop is an infinite loop on a condition and will iterate until that condition is no
longer True.

### Loops: Until
The next loop type we will cover is `until`. This is the opposite of a `while` loop in that it will
wait until a condition is true and iterate until it does.
Not all languages will have this one. This is what they call "syntax sugar" that makes it easier to
write stuff that will do what you want.
If the language you are using doesn't support `until` as a built-in, you can always invert the
operation in a `while` loop.

### Loops: For(start; condition; iterator)
The next type of loop we will consider are called `for` loops. There's a couple of flavours of this
loop. This case is a `for ( start operation; condition; iterator ) do ... end for`.

The start argument is code you want to execute at the start of the loop. This is great for
initalizing variables and setting up the next block of code that is going to execute the loop.

The second argument is the condition upon which we will be iterating the loop. The loop will continue
until this condition is no longer True.

The third argument is the operation that will happen at every iteration.

Everything within this loop block will execute until the conditions are no longer favorable for the
loop.

### Loops: For(x in y)
Most times, when we want to loop over something, it is to iterate over a list of items. This style
of loop lets you do just that by giving you a temporary variable that represents either a key from
within the list of items in the array or a value from the array itself.

Each language will have its style. For example, Python will iterate over the keys and you get the
value like `value = iterator[key]` vs JavaScript which gives you a value from the iterator and you
have to use an enumeration to access the keys.


## Switch/Case/Select
Some languages have this choice operator where you can execute blocks of code depending the result
of an outcome that has a one-to-many relationship. This operation is not present in all languages.
Some require that you use `if()` exclusively. However, enough languages support this construct that
it would be worth mentioning here so you can use it later.

# Conditionals
*If* this condition is true, *then* you will hear a beep. (_beeping-noise_)

Conditionals are the bread and butter of computer programming! This is where "Algebraic English"
comes into play as we are looping from conditions in contained sets called functions.

If I were to sum 90% of the programming out there, functions, conditionals and assignments are
going to be 90% of the code you will write. So, these concepts are absolutely critical.

## And
If two conditions are true, then this "and" operator will return True for both of them.
If either of the conditions are not true, then "and" does not apply, so the result will be False.
At this point, we should be able to deduce that if neither condition is true, then the result will
be False.

## Or
The `or` operator in conditionals is great for checking "if this" or "that".
For example, if both conditions are true, then the result is True.
If either condition is true, then the result is True.
If both conditions are False, then the result is False.














# Control Structures (cont'd)

## Functions
Functions are a control structure that basically wraps functionality into a single executable call
with a name. It's best to write a single function that does one task, and does it well. It's really
easy to go long on a function and wrap a bunch of other functions or operations in it to create a
really long string of thoughts that do a lot of things but accomplish what you want but you don't
really want to create a huge function like that because it'll create a long-running sentence like
this one that hasn't ended until just now.

Creating really long and huge functions are like creating run-on sentences. You don't get a chance
to breathe. It makes it hard to debug. It's almost impossible to Unit Test with value. Without comments,
it can be impossible for others to understand what's going on too.

Try to break your operations into what I call "code paragraphs" or a few function calls or operations
with a clear purpose that can be re-used elsewhere.

This gets into "DRY" or "Don't Repeat Yourself". However, that's a subject I will save for my video
on #SoftwareArchitecture, link in the description and card in the corner.


## Class
Classes are a way to wrap functions in an Object such that they can be called to operate on data.
If the functions are related, share data among them, you may consider a class to wrap those operations
in a single control structure that bundles these operations.

## Package/Module/Namespace
Different languages call these different things. There is a wrapper concept for those that want to
take a set of Class Objects and wrap them into a categorized named format that can be easily accessed
from other modules, packages and namespaces accordingly.


# Conclusion
If you watched this video from start to finish and made it this far, give yourself a huge pat on the
back and smack that like button to give me a pat on the YouTube algorithm!
It took a lot of work to make this video and I'm sure you put in just as much learning the stuff I
put before you here.



























