
# PKI: Public Key Infrastructure
PKI is a set of rules and policies that enables the transfer of information in a secure manner.
It can be as simple and informal as two parties exchanging information securely among themselves,
or it can be a larger integration where a third party validates the sender and recipient via signing
the keys used in the exchange.


## Structure
PKI involves at least two pairs of keys. A public and a private key.
I generate a key pair.
You generate a key pair.

The public key is open to the world and can be shared with anyone.
Anyone can use the public key to encrypt information, or securely lock it so nobody else can read said
data. You can equate the public key to this Master lock in this example.

The private key is yours and yours alone!
*Don't share your privates in public, got it private?*

The private key is used to decrypt anything encrypted with the public key.
The private key is the only way to access data once it's been encrypted with the public key.

This is why folks often say "backup your keys/wallets" in cryptocurrencies.
You never want to be in a single point of failure and lose the only key that can access your data.
So, when you encrypt your data, be sure to make a copy of the password or key that encrypted that data.

## Security
To further enhance the security of this setup, you can optionally encrypt your private key with a password/passphrase.
This is a passphrase that is used to access the private key before decryption takes place.

It's like taking your key and putting it into a mini-safe that requires a PIN to access instead of
just laying on your counter.

Keep in mind: The key is only as safe as your password.

This is why the cryptocommunity advocates using offline storage like a hardware wallet to store your
crypto to avoid the chance at malicious software from ever accessing your private keys.


## Simple Exmple
For a simple example, let's assume we want to exchange information in a secure manner.
In this case: I would send you a copy of my public key. You would send me a copy of your public key.

If I wanted to send you data, I would take your public key, encrypt the data with that public key
and send the result to you. Rest assured nobody will be able to view or intercept the data unless
they have the private key you own, hold and control.

If you want to view the data and interact with it, simply use your private key to decrypt and see
the plain version of the data.

Likewise: If you want to send data to me, then you would use my public padlock I gave to you to encrypt
the data and send it back to me with the confidence that I will be the only one who will have access
to said data via using my private key to decrypt the data.

This relates to cryptocurrency because your wallet is basically a public-private key pair.
When you see that 12 word mnemonic phrase and your wallet tells you to backup that phrase, basically,
that phrase is the private key that is used to generate the wallet.

