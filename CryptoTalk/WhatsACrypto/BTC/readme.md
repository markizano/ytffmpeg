
# BTC: Bitcoin!

## Structure
Bitcoin is a peer-to-peer (P2P) payment network that enables folks to send money to each other
without some intermediate financial institution like a Bank or Broker. Similar to the Tor network,
but with money.

This was setup to avoid needing a trusted third party to validate transactions. That trust can be broken
and manipulated depending on the entity in charge of the financial transactions.

Transactions are secured against double-spending via hashing timestamps along with the transaction
information itself.
Bitcoin is transferred from one party to another via computational power that attempts to collect all
the transactions since the last block and create a new chain of transactions.
The longest chain with the most history is the victorious chain that will have more blocks added to it.
* This is why when you transact on any cryptocurrency network, most often times, you'll see say "your
funds are locked until X number of confirmations"; they want to be certain an attacker doesn't have
the opportunity to "unspend" those coins.

## Proof of Work
Proof of work is when CPU power is expensed to calculate the transactions into a chain. We've covered
this concept in a previous video, but to expand on the previous explanation, let's imagine a tree
instead of a box for a block. As each transaction comes into the network, it's also marked with a
timestamp. These computers are all trying to create a chain of transactions that make sense and includes
as many transactions as it can into the block of transactions.

## Rewards
To incentivize people to secure the network, rewards are granted for the computing power invested
in securing the network.

The genesis block is the first block on the chain and includes the original 50 BTC that was first ever minted.
Every transaction after that is either the transfer of those original 50 BTC, or the minting of 50 new BTC.
Every 210,000 blocks, the rewards are cut in half.

In addition to the block reward, transaction fees are included in the block as well. This will
continue to incentivize people to secure the network even after all blocks have been mined.
Each new block added to the chain includes the block reward as the first transaction, all other transactions
and their fees are added up and sent to the address that found the next block all miners can agree to
start working on next.
The block reward itself is called the Coinbase block. Seems there's a bit of a cooincidence in the name
of the company.

## Transactions
Transactions are made via the PKI infrastructure we talked about in a previous video.
Using this private/public key setup, the recipient is able to sign the request with the public key
and the sender is able to verify it with their private key.
This is why it's absolutely critical you have a secure lock on your private key (e.g. your seed phrase)
because with that, an attacker can completely replicate your wallet, its contents and sign transactions
on your behalf.

## Privacy
Your privacy is secured via the "anonymity" of your public key being open and on the network, but nobody
knowing its you until you associate yourself with that public key as your identity.

## Exploits
Now, let's talk about the security of BitCoin.

An attacker is only ever able to try to reverse transactions where they spent their Bitcoin; Bitcoin
can never just appear out of thin air from an exploited chain of blocks because it would be rejected
by the honest players in the network.

An attacker would need at least 51% of the hashing power of the network to perform an attack.
However, this could only ever be an attack that could "unspend" the coins, or allocate the block reward
to an address they control. This is not beneficial to the attacker because then the coin would lose
its value from the lack of trust in the network.

An attacker can also "guess" at the seed phrase used to generate a wallet. However, this isn't really
practical because they would need that entire nemonic phrase in order to replicate your wallet.

All in all, Bitcoin as a network is actually really secure itself. The exploit vector is you.

# Conclusion
So, Bitcoin itself is very secure and has great incentive to remain as such.
Bitcoin does one thing, and it does it well: Store of value and transfer of that value.

So stay smart. Stay safe. Take care of yourself and others. Think before you click!

