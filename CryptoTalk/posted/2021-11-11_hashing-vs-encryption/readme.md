
# YouTube Opening
Greetings and welcome to Kizano's CryptoTalk. My name is Markizano Draconus, but that is a pen name
for a later story. I am here to talk about all things technology, specifically those related to
understanding cryptocurrency theory. I have an extensive background in information technology from web development
to systems administration and DevOps. If that's something that tickels your fancy, then hit that subscribe
button. Your likes, shares, watch time, and engagement with my content will help me get to a point
where I can produce higher quality content. So share this with a friend if they too are just getting
started.

None of this is financial advice since I am an Edutainment IT channel. I am here to help you understand concepts
through stories, examples and visuals to help get the idea across.

# Hashing vs Encryption
Today, we're going to take a look at the difference between Hashing and Encryption.
It should be a nice and quick video since the explanations can be made relatively simple.

## Hashing
Hashing is one way. You can take any amount of data and reduce it down to a series of hexadecimal
characters that are a fixed length.
Some examples of hashing algorithms include MD5, SHA1, SHA256.

In some cases and for some algorithms like MD5, the results can clash.
Clashing happens when you take more than one input and get the same output.
For an oversimplified example, I input "AAAA" into the MD5 algorithm and get a hash.
I input "CCCCCC" into the algorithm and get the same hash.
You can say there is a clash in the MD5 algorithm between those two values.

For security, you'll want to select an algorithm that has a low number of clashes to avoid
the chances at "reverse hashing" the data you put into the algorithm.

## Reverse Hashing
Reverse hashing is really a term that is coined off this concept here:
- I will execute a bruteforce password cracking attack and create a hash of "a", then "b", then "c".
- I will repeat for "aa", "bb", and "cc".
- I will repat until "zzzzzzzz".

This is called creating a Rainbow Table, in which you get a text file that represents
the hash and the input that created the hash.
So, really it's not "reverse hashing" as much as it's a "reverse table lookup for the hash" to determine
the source of data that went into the algorithm.

## Hashing Examples
Real world example cases of hashing include passwords. As a developer, you should never store passwords
in plaintext. You should always hash them (with a salt) and store the result. If the user enters the
same password and it's correct, the hashes should match. If not, reject the login.

# Encryption
Encryption is the act of taking information and altering the value of that data until its unrecognizable.
An oversimplified example could be to suppose you take the alphabet and reverse the characters. Z is A, B is Y
and so on. The result would appear to be unreadable to anyone who doesn't know the algorithm that went
into encrypting the data.

Encryption is reversable. You need to know the algorithm and the rules that go into that encryption.
Some encryption is really simple and just requires a password.
Other encryptions require a password and a key.
More advanced algorithms require a password, key and IV or Initialization Vector.

## Encryption Keys
An encryption key is not limited to just encryption, but also can be used for authentication and authorization.
In a [previous video](https://blog.markizano.net/2021/11/pki-public-key-infrastructure.html), we covered
the concept of PKI or Public Key Infrastructure. This can also be used to sign the encryption to also
verify the property of key ownership.
If you need to validate identity, then keys will be used to sign the encryption as well to ensure the party
is not only the only one who can view the data, but also the person to whom you think you're speaking.

## Initialization Vector
An Initialization Vector (IV) is basically a seed random number that kicks off the encryption algorithm.
You can think of the IV as the spark plug that starts the encryption engine.

# Summary
So that's hashing vs Encryption in a nutshell. Hashing is one-way and cannot be reversed. However,
there's nothing stopping you from creating a database of hashes to values.
Encryption is reversable, but you need to know the rules of engagement before embarking upon this journey.


# TT: Self Promotion
My name is Markizano Draconus and I teach you about crypto theory.
These concepts will be critical in future videos, so do stay tuned, subscribe and be sure to hit that like button!

# YT: Self Promotion
My name is Markizano Draconus and I teach you about crypto theory.
These concepts will be critical in future videos, so do stay tuned.
If you found anything in this video to be helpful, then smash the like button for the YouTube algorithm.
If you want to learn more about cryptocurrencies and how they work, then join the Kizanonian community
and destroy the subscribe button.
Leave a comment below and let me know what you think and if you want to hear me talk about something
in particular. I look forward to seeing all of you beautiful people on the next video.


Cheers!


