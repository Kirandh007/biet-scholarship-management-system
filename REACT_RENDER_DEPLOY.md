# Deploy AKSHARA BIET React Portal on Render

This repository now includes a professional React + Vite frontend in `client/` and an Express + MongoDB API scaffold in `server/`.

## Frontend Static Site

In Render, create a new **Static Site**.

Use these settings:

```text
Root Directory: client
Build Command: npm install && npm run build
Publish Directory: dist
```

After deploy, Render will give you a public URL for the React portal.

## Backend Web Service Optional

Create a separate **Web Service** if you want the Node.js API.

```text
Root Directory: server
Build Command: npm install
Start Command: npm start
```

Add this environment variable for MongoDB:

```text
MONGODB_URI=your_mongodb_connection_string
```

## Notes

The old Python deployment is still present. For the new premium UI, deploy the `client` folder as a Render Static Site.
