---
title: Concepts
---

# Core Concepts, Explained

## Glossary of Terms

Below is a list of terms and an explanation of how they're used in Tomato.

### Audio Asset
**An <u>audio asset</u> is a short individual audio track** (also referred to as just
an asset). Think individual advertisements, individual public service
announcements, or individual station IDs.

Assets always have a name and underlying audio file (like an mp3) but they can
have additional data like when they begin and end airing, or whether their
enabled at all.

!!! example "Audio Asset Example"
    And example would be a short advertisement audio clip named _"David's
    Steel Guitar Ad."_

### Rotator
**A <u>rotator</u> is a collection of audio assets.** A rotator represents a way
to _categorize_ assets into the same group.

While an asset _can_ belong to more than one rotator, in practice they won't.

!!! example "Rotator Example"
    From the asset example above, you might put _"David's Steel Guitar Ad"_
    along with other short ads for musical instruments in the _"Musical
    Instrument Ads"_ rotator.

### Stop Set
**A <u>stop set</u> is an ordered list of rotators.** A stop set can be thought
of as an entire commercial break, like in traditional radio. To "play" a stop set,
an asset is selected at random[^1] from each rotator in a stop set.

A rotator **can** be (and often is) in a stop set more than once.

If that sounds a bit confusing to you, don't worry. Check out the example below,

!!! example "Stop Set Example"
    Let's say we have the following rotators created, and we've put assets in
    each of them them,

    | Rotator                      | Audio Assets in Rotator                      |
    | ---------------------------: | :------------------------------------------- |
    | Station IDs                  | `S_ID_1.mp3`, `S_ID_2.mp3`, and `S_ID_3.mp3` |
    | Public Service Announcements | `PSA_1.mp3` and `PSA_2.mp3`                  |
    | Advertisements               | `AD_1.mp3`, `AD_2.mp3`, and `AD_3.mp3`       |

    Then we have an  _"Evening Stop Set",_ which contains this an ordered
    list of five rotators, shown here,

    | Order in Stop Set  | Rotator                               |
    | -----: | :------------------------------------ |
    | 1      | Station IDs                           |
    | 2      | Advertisements                        |
    | 3      | Advertisements _(repetition allowed)_ |
    | 4      | Public Service Announcements          |
    | 5      | Station IDs                           |

    Then, when an _"Evening Stop Set"_ is played by Tomato during a commercial
    break, Tomato plays through the following five randomly selected assets.

    | Order in Stop Set | Audio Asset (Randomly Selected)                              |
    | ----------------: | :----------------------------------------------------------- |
    | 1                 | `S_ID_2` &mdash; _selected from Station IDs_                 |
    | 2                 | `AD_3` &mdash; _selected from Advertisements_                |
    | 3                 | `AD_1` &mdash; _selected from Advertisements_                |
    | 4                 | `PSA_2` &mdash; _selected from Public Service Announcements_ |
    | 5                 | `S_ID_1` &mdash; _selected from Station IDs_                 |

### Random Weight
The weight of how likely random selection occurs of an item occurs, when
compared to all other items in a set. The default random weight with Tomato is
always $1$.

Random weight is used when Tomato selects both assets and stop sets.

The likeliness of an item `x` being selected is calculated as follows,

$$
\text{chance of selection of item} = \frac{\text{random weight of item}}{\text{sum all of item random weights}}
$$

!!! example "Random Weight Example"
    If an asset _"Commercial A"_ has a weight of $2$ and all other assets have a
    weight of $1$, then asset _"Commercial A"_ is **twice as likely** to be
    selected when compared to all other assets.

    Suppose there are 26 commercials, named _"Commercial A"_ through
    _"Commercial Z",_ with _"A"_ having a weight of $2$ and the rest having a
    weight of $1$. We get a sum of all random weights as $27$.

    $$
    \begin{align*}
    \text{sum all of item random weights}
        &= \text{Commercial A}_\text{weight} + \text{Commercial A}_\text{weight}
        + \ldots + \text{Commercial Z}_\text{weight} \\
    &= 2 + 1 + \ldots + 1 \\
    &= 27
    \end{align*}
    $$

    Per the selection equation above, the change we'll pick _"Commercial A_"
    with a range weight of $2$ is,

    $$
    \begin{align*}
    \text{Commercial A}_\text{selection chance} &= \frac{\text{Commercial A}_\text{weight}}{\text{sum all of item random weights}} \\
    &= \frac{2}{27} \\
    &\simeq 7.4\%
    \end{align*}
    $$

    Per the selection equation above, the change we'll pick _"Commercial B_"
    with a range weight of $1$ is,

    $$
    \begin{align*}
    \text{Commercial B}_\text{selection chance} &= \frac{\text{Commercial B}_\text{weight}}{\text{sum all of item random weights}} \\
    &= \frac{1}{27} \\
    &\simeq 3.7\%
    \end{align*}
    $$

    So you can see, since $7.4\%$ is twice $3.7\%$, _"Commercial A"_ is **twice
    as likely** to be played as _"Commercial B"_ because of its weight of $2$.



[^1]: The random selection process can be biased by random weight.
