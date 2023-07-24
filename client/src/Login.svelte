<script>
  import { persisted } from "svelte-local-storage-store"

  import { login } from "./stores/connection"

  import tomatoIcon from "../assets/icons/tomato.svg"
  import connectIcon from "../assets/icons/mdi-lan-connect.svg"

  let showPassword = IS_DEV
  let demoMode = false
  let password = ""
  let username = persisted("login-username", "")
  let host = persisted("login-host", "")
  let error = { type: "", message: "" }

  const clearError = () => (error.type = "")

  const submit = async () => {
    try {
      await login($username, password, $host)
    } catch (e) {
      error = e
      console.log(e)
    }
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
    <form class="card-body" on:submit|preventDefault={submit}>
      <div class="form-control items-end">
        <label class="label cursor-pointer space-x-3 pr-0">
          <span class="label-text">
            {#if demoMode}
              <span class="font-bold text-success">Demo mode enabled</span>
            {:else}
              Enable demo mode
            {/if}
          </span>
          <input type="checkbox" class="toggle" />
        </label>
      </div>
      <div class="form-control">
        <div class="label">
          <span class="label-text">Server address</span>
          {#if error.type === "host"}
            <span class="label-text-alt font-bold text-error">{error.message}</span>
          {/if}
        </div>
        <input
          disabled={demoMode}
          bind:value={$host}
          class="input input-bordered"
          placeholder="tomato.example.org"
          type="text"
        />
      </div>
      <div class="flex gap-2">
        <div class="form-control w-full">
          <div class="label">
            <span class="label-text">Username</span>
          </div>
          <input
            disabled={demoMode}
            bind:value={$username}
            class="input input-bordered"
            type="text"
            placeholder="Enter username..."
          />
          {#if error.type === "username"}
            <div class="label">
              <span class="label-text-alt font-bold text-error">{error.message}</span>
            </div>
          {/if}
        </div>
        <div class="form-control w-full">
          <div class="label">
            <span class="label-text">Password</span>
          </div>
          {#if showPassword && !demoMode}
            <input
              disabled={demoMode}
              bind:value={password}
              class="input input-bordered"
              placeholder="Enter password..."
              type="text"
              autocapitalize="none"
              autocomplete="off"
              autocorrect="off"
            />
          {:else}
            <input
              disabled={demoMode}
              bind:value={password}
              class:tracking-wider={(!showPassword || demoMode) && password.length > 0}
              class="input input-bordered"
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
              <input disabled={demoMode} type="checkbox" class="checkbox" bind:checked={showPassword} />
            </label>
          </div>
        </div>
      </div>
      <div class="form-control mt-6">
        <button class="btn btn-primary" type="submit">Login</button>
      </div>
    </form>
  </div>
</div>

<style lang="postcss">
  .tomato-svg > :global(svg) {
    @apply h-20 w-20;
  }
  /* .connect-svg > :global(svg) {
    @apply mr-1.5 h-10 w-10;
  } */
</style>
