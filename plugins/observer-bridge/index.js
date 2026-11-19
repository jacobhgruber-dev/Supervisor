// OpenCode V2 plugin entry point. @opencode/plugin is injected by the host
// for loaded plugins — see lib.mjs for why logic lives there instead of here
// (this file cannot be imported under a plain `node` process).
import { Plugin } from "@opencode/plugin"
import { setup } from "./lib.mjs"

export default Plugin.define({
  id: "observer-bridge",
  setup,
})
