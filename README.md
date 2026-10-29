# Manigent specialist agents

Ready-made specialist agents for [Manigent](https://manigent.ai). Each
folder holds one agent: its role, its field knowledge, the reference material
it works from, its own skills, and a `SOURCES.md` that lists every source it
was adapted from.

An agent is published here only after it beats a strong generalist on
held-out tasks in its field. The comparison is plain Claude with web access
and no role, knowledge or skills. Both arms run several times per task, and
the advantage must hold with any single task removed. Agents still in
development stay out of this repository, and so do the held-out tasks: if
they were published, the comparison could no longer be checked.

## Install one agent

You need the `manigent` runner, signed in to your Manigent account
(`pip install manigent`, or the one-line installer on your Manigent
welcome page). Then:

```bash
manigent agent install --list               # what is here
manigent agent install contract_reviewer    # add one specialist
manigent start --agent contract_reviewer
```

You can also ask your assistant ("can you add a contract reviewer?"); it
runs the same command.

The runner reads this repository at a release tag, never at `main`. The
default tag is pinned in each runner release, so a change pushed here does not
change what an existing runner installs. Every file is checked against the
SHA-256 listed in `setup.json` before anything is written.

Install writes to the agent's home on your computer:

| From the agent folder | To the agent home |
|---|---|
| `role.md` | `knowledge/CLAUDE.md` (its role) |
| `learnings/…` | `memory/learnings/…` (field knowledge it keeps adding to) |
| `knowledge/…` | `knowledge/…` (reference material) |
| `skills/<name>/…` | `personal-skill-hub/skills/<name>/…` (its private skills) |

Running the install again updates the agent. Files that you or the agent
changed since the last install are kept and reported (`--overwrite-local`
replaces them). Nothing is ever deleted.

To install from a fork or a local checkout, use
`manigent agent install <name> --from <url-or-path-to-setup.json>`, or set
`MANIGENT_AGENT_POOL_URL`.

## Layout

```
setup.json        # the install file: every agent, with each file's sha256
LICENSE, NOTICE, LICENSES/
<agent>/
  agent.json      # name, description, capabilities, sample requests
  role.md
  learnings/  knowledge/  skills/
  SOURCES.md      # one row per adapted source (not installed)
```

## Contributing

This repository is generated from the Manigent monorepo, so changes are made
there. Issues and suggestions are welcome here. A new agent, or a change to
an existing one, has to pass the same held-out evaluation before it ships.

## License

Original content is MIT-licensed (`LICENSE`). Some agents adapt third-party
material. Each adapted file keeps its own license (MIT, Apache-2.0 or
CC-BY), and every source is listed in that agent's `SOURCES.md`, pinned to a
commit, with its author and license. Apache-2.0 attributions are in `NOTICE`.
`NOTICE` writes paths as `agents/<name>/…`; in this repository they are at
`<name>/…`. `NOTICE` covers the whole pool, so some of the agents it names may
not be published yet.
