<script>
  import { fade } from "svelte/transition"

  import { progress, sync } from "./stores/store"
  import { address, connected, login, username } from "./stores/connection"

  import tomatoIcon from "../assets/icons/tomato.svg"
  import connectIcon from "../assets/icons/mdi-lan-connect.svg"

  export let connecting = false
  export let password = ""
  export let showPassword = false
  export let errors = { auth: false, address: false }

  export const submit = async () => {
    if (!$address || !$username || !password) {
      if (!$username || !password) errors.auth = "You must enter a username or password"
      if (!$address) errors.address = "You must enter a server address"
      return
    }

    connecting = true
    const { success, error, errorType } = await login(password)
    if (success) {
      if (await sync()) {
        connected.set(true)
      } else {
        errors.address = "Error sync'ing with server"
      }
    } else {
      errors[errorType] = error
    }
    connecting = showPassword = false
  }
</script>

<div class="mx-auto flex min-h-screen w-full max-w-2xl flex-col items-center justify-center space-y-3">
  <div class="flex w-full items-center justify-evenly">
    <div class="tomato-svg">{@html tomatoIcon}</div>
    <div class="flex flex-col items-center space-y-1 font-mono font-bold">
      <h1 class="text-4xl">Tomato</h1>
      <h2 class="text-2xl italic">Radio Automation</h2>
    </div>
    <div class="tomato-svg">{@html tomatoIcon}</div>
  </div>
  <div class="card relative w-full bg-base-300 shadow-2xl">
    {#if connecting}
      <div
        in:fade
        class="absolute inset-0 flex items-center justify-center text-success"
        class:flex-col="{$progress}"
        class:space-y-2="{progress}"
      >
        {#if $progress}
          <div class="radial-progress" style="--value: {$progress.percent}">
            {Math.round($progress.percent)}%
          </div>
        {:else}
          <span class="connect-svg">{@html connectIcon}</span>
        {/if}
        <h2 class="text-3xl italic">Logging in...</h2>
        {#if $progress}
          <span>File {$progress.index} of {$progress.total}</span>
          <span class="max-w-md truncate font-mono text-sm">{$progress.filename}</span>
        {/if}
      </div>
    {/if}
    <form class="card-body" class:invisible="{connecting}" on:submit|preventDefault="{submit}">
      <div class="form-control">
        <div class="label">
          <span class="label-text">Server Address</span>
          {#if errors.address}
            <span class="label-text-alt font-bold text-error">{errors.address}</span>
          {/if}
        </div>
        <input
          bind:value="{$address}"
          class="input-bordered input"
          class:input-error="{errors.address}"
          on:input="{() => (errors.address = false)}"
          placeholder="https://example.org"
          type="text"
        />
      </div>
      <div class="flex gap-2">
        <div class="form-control w-full">
          <div class="label">
            <span class="label-text">Username</span>
          </div>
          <input
            bind:value="{$username}"
            class="input-bordered input"
            class:input-error="{errors.auth}"
            type="text"
            placeholder="Enter username..."
            on:input="{() => (errors.auth = false)}"
          />
          {#if errors.auth}
            <div class="label">
              <span class="label-text-alt font-bold text-error">{errors.auth}</span>
            </div>
          {/if}
        </div>
        <div class="form-control w-full">
          <div class="label">
            <span class="label-text">Password</span>
          </div>
          {#if showPassword}
            <input
              bind:value="{password}"
              class:input-error="{errors.auth}"
              class="input-bordered input"
              on:input="{() => (errors.auth = false)}"
              placeholder="Enter password..."
              type="text"
              autocapitalize="none"
              autocomplete="off"
              autocorrect="off"
            />
          {:else}
            <input
              bind:value="{password}"
              class:input-error="{errors.auth}"
              class:tracking-wider="{!showPassword && password.length > 0}"
              class="input-bordered input"
              on:input="{() => (errors.auth = false)}"
              placeholder="Enter password..."
              type="password"
              autocapitalize="none"
              autocomplete="off"
              autocorrect="off"
            />
          {/if}
          <div class="form-control items-end">
            <label class="label cursor-pointer space-x-3 pr-0">
              <span class="label-text">{showPassword ? "Hide" : "Reveal"} password</span>
              <input type="checkbox" class="checkbox" bind:checked="{showPassword}" />
            </label>
          </div>
        </div>
      </div>
      <div class="form-control mt-6">
        <button class="btn-primary btn" type="submit">Login</button>
      </div>
    </form>
  </div>
</div>

<style lang="postcss">
  .tomato-svg > :global(svg) {
    @apply h-20 w-20;
  }
  .connect-svg > :global(svg) {
    @apply mr-1.5 h-10 w-10;
  }
</style>
