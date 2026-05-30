# Custom frontend drop-in

If a `@wger-project/react-components` tarball (`*.tgz`) is placed in this
directory, the production Docker image will use it **instead of** pulling the
published package from npm. This is how the customized React frontend (the fork
with the ready-made-meals UI) gets baked into the image.

To produce the tarball from the React fork (`../wger-react`):

```
# node_modules in a named volume to avoid OneDrive/host churn
docker run --rm \
  -v "/abs/path/to/wger-react:/app" \
  -v wger_react_nm:/app/node_modules \
  -w /app node:22 \
  sh -lc "npm ci && npm run build && npm pack"

# copy the resulting tgz here
cp /abs/path/to/wger-react/wger-project-react-components-*.tgz frontend/
```

Then build the wger image normally; it will detect and use this tarball.
If no tarball is present here, the build falls back to the npm package.
