# How we’re making GitHub Copilot smarter with fewer tools

Home / AI & ML / GitHub Copilot

# How we’re making GitHub Copilot smarter with fewer tools

We’re using embedding-guided tool routing, adaptive clustering, and a
streamlined 13-tool core to deliver faster experience in VS Code.

Anisha Agarwal & Connor Peet

November 19, 2025

| 7 minutes

  * Share: 
  *   *   * 

In VS Code, GitHub Copilot Chat can access hundreds of tools through the Model
Context Protocol (MCP) that range from codebase analysis tools to Azure-
specific utilities. But giving an agent too many tools doesn’t always make it
smarter. Sometimes it just makes it slower.

If you’ve ever seen this spinner in VS Code, you’ve hit the limits of a model
that’s trying to reason across too many tools at once.

To fix that, we’ve built two new systems—embedding-guided tool routing and
adaptive tool clustering—and we’re rolling out a reduced toolset that trims
the default 40 built-in tools down to 13 core ones. Across benchmarks like
SWE-Lancer and SWEbench-Verified with both GPT-5 and Sonnet 4.5, these changes
improve success rates by 2-5 percentage points. In online A/B testing, it
reduces response latency by an average of 400 milliseconds.

## Too many tools impede agent intelligence

The default toolset in VS Code consists of about 40 built-in tools, ranging
from general command-line utilities to specialized tools for Jupyter
Notebooks. With MCP servers included, that number can grow into the hundreds.
Often, MCP servers bring in so many tools that they can exceed the API limits
of some models.

We’ve explored ways to filter down our toolset to provide only the tools most
relevant to the user’s query, while not restricting the agent’s capabilities.
Specifically, we needed to make sure we didn’t sacrifice the user’s experience
to achieve lower latency.

To accomplish this, we designed a middle-ground approach: “virtual tools.”
This includes functionally grouping similar tools under one “virtual tool” the
chat agent can expand as needed. Think of these as directories that contain
related tools. This gives the model a general sense of what’s available
without flooding it with hundreds of tool names. It also reduces the cache
miss rate we’d expect if the model searched for individual tools, since it’s
likely that similar tools are used and activated together.

## Applying lossless dynamic tool selection for MCP tools

### Adaptive tool clustering

Initially we fed all the available tools into an LLM and asked it to group and
summarize them. But this had two big issues:

  * We couldn’t control the number of groups created, and it sometimes exceeded model limits 
  * It was extremely slow and incurred a huge token cost. The model would also sometimes ‘forget’ to categorize certain tools, forcing retries 

To tackle this issue, we applied our internal Copilot embedding model
optimized for semantic similarity tasks to generate embeddings for each tool
and group them using cosine similarity. This clustering method allowed
precise, stable, and reproducible groups. As an example, here is one possible
grouping of embeddings for the GitHub MCP server’s tools in the embedding
space:

We still use a model call to summarize each cluster, but this step is much
faster and cheaper than asking the model to categorize everything from
scratch. Tool embeddings and group summaries are cached locally, so
recomputing them is comparatively cheap.

## Context-guided tool selection

Once tools were grouped, we faced another problem: how does the model know
which group to open without checking them all? We saw that, most of the time,
the model would  _eventually_ find the right tool for its task. However, each
call to a virtual tool still results in a cache miss, an extra round trip, and
an opportunity for a small percentage of agent operations to fail.

For example, when the user says:  _“Fix this bug and merge it into the dev
branch.”_

The model often opens **search tools** , then **documentation tools** , then
**local Git tools** , before finally realizing that it actually needs the
**merge tool inside the GitHub MCP tool group** to complete the operation.

Each incorrect group lookup adds latency and overhead, even though the correct
group is fairly obvious from the context.

To address this, we introduced **Embedding-Guided Tool Routing**. Before any
tool group is expanded, the system compares the query embedding against vector
representations of all tools (and their clusters), allowing it to pre-select
the most semantically relevant candidates—even if they’re buried deep inside a
group.

With context-aware routing, we can infer from the beginning that the model is
very likely to need the  _merge tool_ inside the GitHub MCP tool group, and
include it directly in its candidate set—eliminating unnecessary exploratory
calls and significantly reducing latency and failure rates.  
  
By surfacing only the most promising matches, we make the model’s search more
targeted and reliable, while reducing redundant exploration.

## Embedding-based selection (powered by the Copilot Embedding model)

We calculate the success of our embedding-based selection process via **Tool
Use Coverage,** which measures how often the model already has the right tool
visible when it needs it.

In benchmarks, the embedding-based approach achieved 94.5% Tool Use Coverage,
outperforming both LLM-based selection (87.5%) and the default static tool
list (69.0%).

**Offline** , this approach resulted in a 27.5% absolute improvement in
coverage, clearly surpassing the LLM-based method while helping the agent
reason faster and stay efficient.

**Online testing** shows the same pattern: only **19%** of Stable tool calls
were successfully pre-expanded using the old method, whereas **72%** of
Insiders tool calls were pre-expanded thanks to the embedding-based matching.
This confirms that the gains observed offline are consistently reflected in
real-world usage.

## Less is more: shrinking the default toolset

Even without hitting the model limits that massive MCP servers can trigger, an
oversized built-in toolset still degrades performance. In offline benchmarks,
we observed a 2–5 percentage point decrease in resolution rate on benchmarks
including SWE-Lancer when the agent had access to the full built-in toolset.
Behaviorally, the agent ends up ignoring explicit instructions, using tools
incorrectly, and calling tools that are unnecessary to the task at hand.

So, we trimmed the list. Based on tool usage statistics and performance data,
we identified a core toolset of 13 essential tools. These tools encompass
high-level repository structure parsing, file reading and editing, context
searching, and terminal usage.

The remaining, non-core built-in tools are grouped into four virtual
categories: Jupyter Notebook Tools, Web Interaction Tools, VS Code Workspace
Tools, and Testing Tools. This way, the model sees the smaller core set up-
front and can expand groups only if necessary. As a result, users with the
shrunken toolset experience an average decrease of 190 milliseconds in TTFT
(Time To First Token), and an average decrease of 400 milliseconds in TTFT
(Time to Final Token, or time to complete model response).

A smaller toolset enables the agent to be more effective: simpler reasoning,
faster response times, and better performance.

## Future directions: from tool selection to long-context reasoning

As MCP systems evolve, the challenge isn’t just picking the right tool—it’s
reasoning across time, context, and interactions.

A truly intelligent model shouldn’t just react to queries; it should
_remember previous tool usage, infer intent from history, and plan multi-step
actions_ over long sessions. In this sense, tool selection is an early form of
long-context reasoning. The same mechanisms that help models route to the
right tool today could, in the future, help them reason across thousands of
turns helping them decide when to act, when to delegate, and when to stop.

Our next step is to explore how embeddings, memory, and reinforcement signals
can combine to create context-aware agents that learn  _how_ to use tools, not
just  _which_ ones to pick.

**Want to see how Copilot uses MCP tools in action?** Try GitHub Copilot now >

**Acknowledgments**

A big shoutout to our developer community for continuing to give us feedback
and push us to deliver the best possible agent experiences with GitHub
Copilot. A huge thanks also to Zijian Jin, a researcher on the team who helped
to write this blog—and to the researchers, engineers, product managers across
VS Code and GitHub Copilot for this work. (Also: We’re hiring applied
researchers and software engineers, so feel free to apply!)

* * *

## Tags:

  * agentic workflows 
  * GitHub Copilot 
  * MCP 
  * VS Code 

##  Written by

Applied Scientist II

Principal Software Engineer

##  Related posts

AI & ML

###  Evolving GitHub Copilot’s next edit suggestions through custom model
training

GitHub Copilot’s next edit suggestions just got faster, smarter, and more
precise thanks to new data pipelines, reinforcement learning, and continuous
model updates built for in-editor workflows.

Kevin Merchant & Yu Hu

AI & ML

###  How to write a great agents.md: Lessons from over 2,500 repositories

Learn how to write effective agents.md files for GitHub Copilot with practical
tips, real examples, and templates from analyzing 2,500+ repositories.

Matt Nigh

AI & ML

###  Unlocking the full power of Copilot code review: Master your instructions
files

Discover practical tips, examples, and best practices for writing effective
instructions files. Whether you’re new or experienced, you’ll find something
to level up your code reviews.

Ria Gopu

##  Explore more from GitHub

###  Docs

Everything you need to master GitHub, all in one place.

Go to Docs

###  GitHub

Build what’s next on GitHub, the place for anyone from anywhere to build
anything.

Start building

###  Customer stories

Meet the companies and engineering teams that build with GitHub.

Learn more

###  The GitHub Podcast

Catch up on the GitHub podcast, a show dedicated to the topics, trends,
stories and culture in and around the open source developer community on
GitHub.

Listen now

## We do newsletters, too

Discover tips, technical guides, and best practices in our biweekly newsletter
just for devs.

Your email address

Your email address

Subscribe

Yes please, I’d like GitHub and affiliates to use my information for
personalized communications, targeted advertising and campaign effectiveness.
See the GitHub Privacy Statement for more details.

Subscribe

