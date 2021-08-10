---
sidebar_position: 7
label: This website
---
# About this documentation website

This website was built using **[Docusaurus](https://docusaurus.io/)**, following the guide of this **[tutorial](https://www.youtube.com/watch?v=I-hYKNgaMmE)**.
Then, we have linked Netlify to GitHub <code>Deploy>Deploy Settings>Link to GitHub</code>. In our case, since the documentation website is under the docs folder in our repo, the base directory is <code>docs</code>. The build command is <code>yarn build</code>, and the publish directory is <code>docs/build</code>.

If you want to use LaTeX for rendering mathematical equations, you can install **[KaTex](https://katex.org/docs/cli.html)** 

```
npm install katex
```
And then follow this **[guide](https://docusaurus.io/docs/markdown-features/math-equations)**  