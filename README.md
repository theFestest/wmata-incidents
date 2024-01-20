
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

https://github.com/MarshalX/atproto/blob/main/examples/advanced_usage/send_rich_text.py

https://github.com/susumuota/nanoatp

## Demo

https://python-hello-world.vercel.app/

## Running Locally

```bash
npm i -g vercel
vercel dev
```

Your Python API is now available at `http://localhost:3000/api`.

## TODO:

- integrate newer api features: https://github.com/MarshalX/atproto/releases/tag/v0.0.34

- fix post time zone

- Decide to keep or remove vercel compatability

- Simplify vercel layout (remove silly additions from messing with cron triggers)

- Support reposting long standing incidents (such as Green line currently) once a day or so.
    - perhaps: if incident is older than 24 hours and time is within 1 interval of 8 am or 4 pm (commuting hours)?

- Let manual posts not interfere with running (tag specifically bot posts, or pull more posts if the latest doesn't contain the time)

- Trim spaces at the start/end of lines? avoid whatever caused this: https://bsky.app/profile/wmata-incidents.bsky.social/post/3k3ilx2ejfl2v
    - modify dedent to not have \n interfere with it
    - issue was: 'Description': 'Some D14 trips may be delayed due to operator availability. Check where your bus is at \nhttps://buseta.wmata.com/#D14'
    - see https://github.com/theFestest/wmata-incidents/actions/runs/5678804071/job/15389726708

- Consider replacing internal newlines in provided info to preserve formatting

- Retry posting without facets if posting with facets fails?

- Make errors / error-reporting more visible
