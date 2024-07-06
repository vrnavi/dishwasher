<p align="center">
    <a href="https://3gou.0ccu.lt"><picture><img width="150px" src="https://raw.githubusercontent.com/vrnavi/sangou/master/sangou/assets/sangou.png"></picture></a>
</p>
<p align="center"><i>三号 - Sangou</i></p>

<p align="center"><a href="https://github.com/vrnavi/sangou/releases/latest"><img alt="Stable Version" src="https://img.shields.io/badge/Stable-0.3.2-cyan?labelColor=black"></a> <a href="https://codeload.github.com/vrnavi/sangou/zip/refs/heads/master"><img alt="Nightly Version" src="https://img.shields.io/badge/Nightly-0.4.0-lightpink?labelColor=black"></a> <a href="https://github.com/vrnavi/sangou/commits/master/"><img alt="GitHub Activity" src="https://img.shields.io/github/commit-activity/w/vrnavi/sangou?logo=github&color=white&labelColor=black&label=Commits"></a> <a href="https://github.com/vrnavi/sangou/graphs/contributors"><img alt="GitHub Contributors" src="https://img.shields.io/github/contributors/vrnavi/sangou?color=lightpink&labelColor=black&label=Contribs"></a> <a href="https://github.com/vrnavi/sangou/blob/master/LICENSE"><img alt="GitHub License" src="https://img.shields.io/github/license/vrnavi/sangou?color=cyan&labelColor=black&label=License"></a></p>


- Sangou is a "rebellious" Discord bot, using [robocop-ng](https://github.com/reswitched/robocop-ng) as a loose base. He was made for the OneShot Discord, but is free to use.
- Sangou is currently in heavy development, and has countless features that are subject to change. **Self hosting of him is not advised.** I cannot stop you, however.
- No support from me will be given to self-hosted variations of Sangou. Updating self-hosted versions may break without warning. Support is given to the main bot.
- Features are added to and removed from Sangou at my whim, however the goal is for a "Kitchen Sink" compatible bot. The goal is to have Sangou "feature complete" at `1.0.0`.

---

# Usage

To use the publicly available Sangou bot, please ask in the support server, findable in the [Documentation](https://3gou.0ccu.lt/).

In hosting the bot yourself, you accept that you are on your own. To do so, follow these simple instructions.

- Download the bot from this repository. Stick to the release versions unless you have encountered a bug.
- Install [pipenv](https://pipenv.pypa.io/en/latest/).
- Use `pipenv install` in the root folder, where `Pipfile` is.
- Copy `config.example.py` to `config.py`, and fill it out with your bot information.
- Enter `pipenv shell`, `cd sangou`, then `python __init__.py`.
- Congratulations.

I will not help you if you wish to use something other than pipenv..
