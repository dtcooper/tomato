---
title: Concepts
---

# Core Concepts, Explained

Below is a list of concepts and an explanation of how they're used in Tomato.


## Audio Entities

Tomato's audio entities are a core concept, and they're defined below.

### Audio Asset
**An <u>audio asset</u> is a short individual audio track** (called **an asset**
for short). Think individual advertisements, individual public service
announcements, or individual station IDs.

Assets always have a name and underlying audio file (like an mp3) but they can
have additional data for example when they begin and end airing.

!!! example "Audio Asset Example"
    A short advertisement audio clip named _"David's Steel Guitar Ad."_

### Rotator
**A <u>rotator</u> is a collection of _similar_ audio assets.** A rotator is how
you to _categorize_ assets into a group.

While an asset _can_ belong to more than one rotator, in practice they shouldn't.

!!! example "Rotator Example"
    From the asset example above, you might put _"David's Steel Guitar Ad"_
    along with other short ads for musical instruments in the _"Musical
    Instrument Ads"_ rotator.

### Stop Set
**A <u>stop set</u> is an ordered list of rotators.** A stop set can be thought
of as an entire commercial break, like what you'd hear in traditional radio. In
order to play a stop set, an asset is selected at random[^1] from each rotator
in it.

A rotator **can** be (and often is) in a stop set more than once. Think having
station ID jingles at the start and end of a stop set, as in the example below.

???+ example "Stop Set Example"
    If stop sets are a bit confusing to you, don't worry. Follow along.

    Let's say we have the following rotators created, and we've put assets in
    each of them them,

    ```mermaid
    flowchart TD
        sids(Station IDs<br><em>Rotator</em>)
        psas(Public Service Announcements<br><em>Rotator</em>)
        ads(Advertisements<br><em>Rotator</em>)
        sid1(S_ID_1.mp3<br><em>Asset</em>)
        sid2(S_ID_2.mp3<br><em>Asset</em>)
        sid3(S_ID_3.mp3<br><em>Asset</em>)
        sid1 --> sids
        sid2 --> sids
        sid3 --> sids
        psa1(PSA_1.mp3<br><em>Asset</em>)
        psa2(PSA_2.mp3<br><em>Asset</em>)
        psa1 --> psas
        psa2 --> psas
        ad1(AD_1.mp3<br><em>Asset</em>)
        ad2(AD_2.mp3<br><em>Asset</em>)
        ad3(AD_3.mp3<br><em>Asset</em>)
        ad1 --> ads
        ad2 --> ads
        ad3 --> ads
    ```

    Then we have an  _"Evening Stop Set",_ which contains this an ordered list
    of five rotators, shown here,

    ```mermaid
    flowchart RL
        stopset(Evening Stop Set)
        subgraph "Rotators in stop set"
            direction TB
            rotator1("#8291;1. Station IDs<br><em>Rotator</em>")
            rotator2("#8291;2. Advertisements<br><em>Rotator</em>")
            rotator3("#8291;3. Advertisements<br><em>Rotator</em><br><strong><small>Repetition Allowed!</small></strong>")
            rotator4("#8291;4. Public Service Announcements<br><em>Rotator</em>")
            rotator5("#8291;5. Station IDs<br><em>Rotator</em>")
        end
        rotator1 --- stopset
        rotator2 --- stopset
        rotator3 --- stopset
        rotator4 --- stopset
        rotator5 --- stopset
    ```

    Then, when an _"Evening Stop Set"_ is generated and played by Tomato during
    a commercial break, here's what's played.

    ```mermaid
    flowchart LR
        subgraph "Rotators in stop set"
            direction TB
            rotator1("#8291;1. Station IDs<br><em>Rotator</em>")
            rotator2("#8291;2. Advertisements<br><em>Rotator</em>")
            rotator3("#8291;3. Advertisements<br><em>Rotator</em>")
            rotator4("#8291;4. Public Service Announcements<br><em>Rotator</em>")
            rotator5("#8291;5. Station IDs<br><em>Rotator</em>")
        end
        stopset(Evening Stop Set)
        subgraph "Assets played (generated)"
            direction TB
            asset1(S_ID_2.mp3<br><em>Asset</em>)
            asset2(AD_3.mp3<br><em>Asset</em>)
            asset3(AD_1.mp3<br><em>Asset</em>)
            asset4(PSA_2.mp3<br><em>Asset</em>)
            asset5(S_ID_1.mp3<br><em>Asset</em>)
        end
        rotator1 --- stopset
        rotator2 --- stopset
        rotator3 --- stopset
        rotator4 --- stopset
        rotator5 --- stopset
        asset1 -- randomly<br>selected<br>from rotator --- rotator1
        asset2 -- randomly<br>selected<br>from rotator --- rotator2
        asset3 -- randomly<br>selected<br>from rotator --- rotator3
        asset4 -- randomly<br>selected<br>from rotator --- rotator4
        asset5 -- randomly<br>selected<br>from rotator --- rotator5
    ```

    !!!note "Stop sets and ***generated*** stop sets"

        Note, the above is a so-called "generated" stop set. It's an actual stop set
        that is played in the desktop client. We refer to these as _generated_
        because Tomato picks (or generates) individual assets to play.

### Relationship Diagram

Here's a simple relationship diagram for the entities described above.

```mermaid
flowchart RL
    stopset{Stop Sets}
    rotator{Rotators}
    asset{Audio Assets}
    rotator -- "many-to-many<br>relationship (ordered list)" --> stopset
    asset -- "many-to-many<br>relationship (set)" --> rotator
```

## Wait Interval

Tomato's **wait interval** is how long the desktop app should wait before
notifying the user that a stop set is due to be played.

## Weight
**<u>Weight</u> (or random weight) is how likely random selection of an item occurs**,
when compared to all other items of the same type. The default weight of an item
with always $1$ unless modified.

Random weight is used when Tomato selects both assets and stop sets.

The likeliness (or "chance") of an item $x$ being selected is calculated as follows,

$$
x_{\text{chance}} = \frac{x_{\text{weight}}}{[\text{sum all of item weights}]}
$$


???+ example "Weight Example"
    Let's dig a little deeper. For the purposes of this example, all assets are
    in a rotator called _"Commercials."_

    If an asset named _"Commercial A"_ has a weight of $2$ and all other assets
    have a weight of $1$, then asset _"Commercial A"_ is **twice as likely** to
    be selected when compared to all other assets.

    Suppose there are 26 commercials &mdash; one for each letter of the alphabet
    &mdash; and they're named _"Commercial A"_ through _"Commercial Z"_.

    We assign a weight of $2$ to _"Commercial A,"_ or $\text{A}_\text{weight} = 2$
    and assign a weight of $1$ to _"Commercial B"_ through _"Commercial Z,"_
    or $\text{B}_\text{weight} = 1,\ \text{C}_\text{weight} = 1,\ \ldots,\
    \text{X}_\text{weight} = 1,\ \text{Z}_\text{weight} = 1$.

    We get a sum of all random weights as $27$, illustrated below,

    $$
    \begin{align*}
    [\text{sum all of item weights}] &= \sum_{x=A}^{Z} x_\text{weight} \\
    &= \text{A}_\text{weight} + (\text{B}_\text{weight} + \text{C}_\text{weight}
        + \ldots + \text{X}_\text{weight} +  \text{Z}_\text{weight}) \\
    &= 2 + (1 + 1 + \ldots + 1 + 1) \\
    &= 2 + 25 \\
    &= 27
    \end{align*}
    $$

    Then, per the selection equation above,

    $$
    \begin{align*}
    \text{A}_\text{chance} &= \frac{\text{A}_\text{weight}}{\text{
        [sum all of item weights]}} \\
    &= \frac{2}{27} \\
    &= 7.4\%
    \end{align*}
    $$

    So the chance we'll pick _"Commercial A_" with a random weight of $2$ is
    $\text{A}_\text{chance} = 7.4\%$. Similarly,

    $$
    \begin{align*}
    \text{B}_\text{chance} &= \frac{\text{B}_\text{weight}}{\text{[sum all of item weights]}} \\
    &= \frac{1}{27} \\
    &= 3.7\%
    \end{align*}
    $$

    The chance we'll pick _"Commercial B_" with a weight of $1$ is
    $\text{B}_\text{chance} = 3.7\%$

    So as you can see, since $7.4\%$ is twice $3.7\%$, _"Commercial A"_ with
    weight $2$ is **twice as likely** to be played as _"Commercial B"_ with
    weight $1$.



## Anti-Repeat Algorithm

Tomato tries _very_ hard not to repeat playing the same asset too soon. There
are several sets of assets that can potentially be ignored as defined below.

$\text{ignores}_\text{soft} = [\text{assets played recently (within NO_REPEAT_ASSETS_TIME)}]$

$\text{ignores}_\text{medium} = [\text{assets on another generated stop set within current playlist}]$

$\text{ignores}_\text{hard} = [\text{assets that exist as previous entries in current generated stopset}]$

!!!note
    $\text{ignores}_\text{soft}$ will be an empty set if `NO_REPEAT_ASSETS_TIME = 0`

So $\text{ignores}_\text{soft}$ are _stuff that's played recently_, $\text{ignores}_\text{medium}$
are _stuff that's going to play later in the playlist_, and $\text{ignores}_\text{hard}$ are _assets in
the current stopset._

Suppose Tomato is ready to select an asset from a rotator. Tomato will attempt
to ignore assets by trying to ignore them using the priority order as defined below.
That's to say, it'll go through several _tries_ to ignore assets. If Tomato can't
select an asset, it'll proceed to the next try.

Starting with the set of all _eligible_ assets  in a rotator (enabled and valid air dates),

* Try #1: Ignore all assets in $\text{ignores}_\text{soft} \cup \text{ignores}_\text{medium} \cup \text{ignores}_\text{hard}$
* Try #2: Ignore all assets in $\text{ignores}_\text{medium} \cup \text{ignores}_\text{hard}$
* Try #3: Ignore all assets in $\text{ignores}_\text{hard}$
* Try #4 (only if `ALLOW_REPEATS_IN_STOPSET = True`): Choose an asset from complete set of eligible assets
* Fail (no asset selected).


[^1]: The random selection process can be biased by random [weight](#weight) and
    the [anti-repeat algorithm](#anti-repeat-algorithm)
