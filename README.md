
# WMATA Incidents Bot

https://bsky.app/profile/wmata-incidents.bsky.social

## References

https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python

https://vercel.com/docs/cron-jobs#cron-expressions

https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python

https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python#python-dependencies

https://cloud.google.com/scheduler/docs/creating#begin

https://developer.wmata.com/docs/services/54763641281d83086473f232/operations/54763641281d830c946a3d77?

https://twitter.com/wmata

https://twitter.com/metrorailinfo

https://www.wmata.com/service/status/index.cfm#current-alerts

https://wmata.com/initiatives/Open-Data-Hub/MetroPulse.cfm

https://www.pythonmorsels.com/dedent/

## Demo

https://python-hello-world.vercel.app/

## Running Locally

```bash
npm i -g vercel
vercel dev
```

Your Python API is now available at `http://localhost:3000/api`.

## TODO:

- Increase frequency of checks (is 5 minutes enough? can go higher on some platforms if needed)

- Consider making post text shorter / more compact

- Enable elevator incidents

- Maybe: remove state via kv store and just check past interval (requires good scheduling to not miss any; might repeat posts sometimes)

- Maybe: keep state but only store the date of the most recent posted update. Then post everything newer than that update.

- Maybe: simply check own feed, and post anything newer than the timestamp of the last post (might miss anything between api check and post)
    - better parse the timestamp of the update out of the last post!

- Decide to keep or remove vercel compatability

- Simplify vercel layout (remove silly additions from messing with cron triggers)

- Make urls clickable via rich text (https://github.com/MarshalX/atproto/blob/main/examples/advanced_usage/send_rich_text.py)
    - use detectFacets ? https://github.com/susumuota/nanoatp
    - or just find start byte as "https://" and end byte as first whitespace after url? (might be too naive)

- Support reposting long standing incidents (such as Green line currently) once a day or so.
    - perhaps: if incident is older than 24 hours and time is within 1 interval of 8 am or 4 pm (commuting hours)?

- Let manual posts not interfere with running (tag specifically bot posts, or pull more posts if the latest doesn't contain the time)

