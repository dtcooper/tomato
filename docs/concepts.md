---
title: Concepts
---

# Core Concepts, Explained

## Glossary of Terms

Audio Asset
:   A short, individual audio track. Think individual advertisements, individual
    public service announcements, or individual station IDs.

    Audio assets always have a name and underlying audio file, like an mp3 but
    can contain additional data like when they begin and end airing, or whether
    their enabled at all.

    !!! example "Audio Asset Example"
        And example would be a short advertisement audio clip named _"David's
        Steel Guitar Ad."_

Rotator
:   A collection of audio assets. A rotator represents a way to _categorize_
    audio assets into the same group.

    An audio asset **can** belong to more than one rotator, but in practice,
    they won't.

    !!! example "Rotator Example"
        From the audio asset example above, you might put _"David's Steel
        Guitar Ad"_ along with other short ads for musical instruments in the
        _"Musical Instrument Ads"_ rotator.

Stop Set
:   A stop set is an ordered list of rotators. A stop set can be thought of as
    an entire commercial break, like in traditional radio. One audio asset is
    selected at random[^1] for each rotator in a stop set.

    A rotator **can** can be in a stop set more than once.

    If that sounds a bit confusing to you, see the example below.

    !!! example "Stop Set Example"
        Let's say we have the following rotators, each several audio assets in
        them,

        | Rotator                      | Audio Assets in Rotator          |
        | ---------------------------: | :------------------------------- |
        | Station IDs                  | `S_ID_1`, `S_ID_2`, and `S_ID_3` |
        | Public Service Announcements | `PSA_1`, `PSA_2`, and `PSA_3`    |
        | Advertisements               | `AD_1`, `AD_2`, and `AD_3`       |

        Then we have an  _"Evening Stop Set",_ which contains this an ordered
        list of five rotators, shown here,

        | Index  | Rotator                               |
        | -----: | :------------------------------------ |
        | 1      | Station IDs                           |
        | 2      | Advertisements                        |
        | 3      | Advertisements _(repetition allowed)_ |
        | 4      | Public Service Announcements          |
        | 5      | Station IDs                           |

        Then, when an _"Evening Stop Set"_ is generated to be played by Tomato
        during a commercial break, Tomato plays through the following five
        randomly selected audio assets.

        | Index  | Audio Asset (Randomly Selected)                            |
        | -----: | :--------------------------------------------------------- |
        | 1      | `S_ID_2` &mdash; selected from Station IDs                 |
        | 2      | `AD_3` &mdash; selected from Advertisements                |
        | 3      | `AD_1` &mdash; selected from Advertisements                |
        | 4      | `PSA_2` &mdash; selected from Public Service Announcements |
        | 5      | `S_ID_1` &mdash; selected from Station IDs                 |

Random Weight
:   Random weight is also known as selection bias.


[^1]: The random selection process can be biased by weight.
