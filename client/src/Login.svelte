<script>
  import dayjs from "dayjs"
  import fullscreenExit from "@iconify/icons-mdi/fullscreen-exit"
  import fullscreenIcon from "@iconify/icons-mdi/fullscreen"
  import lanDisconnect from "@iconify/icons-mdi/lan-disconnect"

  import { persisted } from "svelte-local-storage-store"

  import { isFullscreen, setFullscreen } from "./stores/config"
  import { conn, login, protocolVersion, hasInternet } from "./stores/connection"

  import { tomatoIcon, isDev, urlParams, isPackaged } from "./utils"

  import Icon from "./components/Icon.svelte"
  import SyncModal from "./main/modals/Sync.svelte"

  let showPassword = isDev
  let demoMode = false
  // Sane defaults for non-packaged dev mode development
  let password = isDev && !isPackaged ? "tomato" : ""
  let username = persisted("login-username", isDev && !isPackaged ? "tomato" : "")
  let host = persisted("login-host", isDev && !isPackaged ? "localhost" : "")
  let showSyncModal

  let error = { type: urlParams.errorType || "", message: urlParams.errorMessage || "" }

  const clearError = () => (error = { type: "", message: "" })

  $: formDisabled = $conn.connecting || $conn.connected
  $: showSyncModal = !$conn.ready && $conn.connected

  const submit = async () => {
    clearError()
    if (!isDev) {
      showPassword = false
    }
    if ($conn.connecting) {
      return
    }

    if (demoMode) {
      error = { type: "host", message: "Demo mode not yet enabled." }
    } else {
      try {
        await login($username, password, $host)
      } catch (e) {
        error = e
      }
    }
  }
</script>

<SyncModal title="Connecting" isFromLogin={true} show={showSyncModal} />

<!-- Fixed fullscreen toggle for login only (z-index of modal is 9999) -->
<div class="fixed right-2 top-2 z-[10000]">
  <div class="tooltip tooltip-left tooltip-info flex" data-tip={`${$isFullscreen ? "Exit" : "Enter"} fullscreen mode`}>
    <button class="btn btn-circle btn-ghost" on:click={() => setFullscreen(!$isFullscreen)} tabindex="-1">
      <Icon icon={$isFullscreen ? fullscreenExit : fullscreenIcon} class="h-8 w-8" />
    </button>
  </div>
</div>

<div
  class="mx-auto flex min-h-screen w-full max-w-2xl flex-col items-center justify-center gap-y-3"
  class:cursor-wait={$conn.connecting}
>
  <div class="flex w-full items-center justify-evenly">
    <Icon icon={tomatoIcon} class="h-20 w-20" shape-rendering="crispEdges" viewBox="0 -.5 16 16" />
    <div class="flex flex-col items-center space-y-1 font-mono font-bold">
      <h1 class="text-4xl">Tomato</h1>
      <h2 class="text-2xl italic">Radio Automation</h2>
    </div>
    <Icon icon={tomatoIcon} class="h-20 w-20" shape-rendering="crispEdges" viewBox="0 -.5 16 16" />
  </div>
  <div class="card relative w-full bg-base-300">
    <form class="card-body" on:submit|preventDefault={submit}>
      <!-- For demo mode
        <div class="form-control items-end">
          <label class="label cursor-pointer space-x-3 pr-0">
            <span class="label-text">
              {#if demoMode}
                <span class="font-bold text-success">Demo mode enabled</span>
              {:else}
                Enable demo mode
              {/if}
            </span>
            <input type="checkbox" class="toggle" bind:checked={demoMode} />
          </label>
        </div>
      -->
      <div class="form-control">
        <div class="label">
          <span class="label-text flex items-center gap-2">
            Server address
            {#if !$hasInternet}
              <div
                class="tooltip tooltip-bottom tooltip-warning"
                data-tip="You appear to be disconnected from the Internet. Your server may be unavailable."
              >
                <Icon icon={lanDisconnect} class="h-5 w-5 text-warning" />
              </div>
            {/if}
          </span>
          {#if error.type === "host"}
            <span class="label-text-alt font-bold text-error">{error.message}</span>
          {/if}
        </div>
        <input
          disabled={formDisabled}
          on:input={clearError}
          class:input-error={error.type == "host"}
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
            disabled={formDisabled}
            on:input={clearError}
            bind:value={$username}
            class:input-error={error.type == "userpass"}
            class="input input-bordered"
            type="text"
            placeholder="Enter username..."
          />
          {#if error.type === "userpass"}
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
              disabled={formDisabled}
              bind:value={password}
              on:input={clearError}
              class:input-error={error.type == "userpass"}
              class="input input-bordered"
              placeholder="Enter password..."
              type="text"
              autocapitalize="none"
              autocomplete="off"
              autocorrect="off"
            />
          {:else}
            <input
              disabled={formDisabled}
              bind:value={password}
              on:input={clearError}
              class:input-error={error.type == "userpass"}
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
            <label class="label cursor-pointer gap-x-3 pr-0">
              <span class="label-text">{showPassword ? "Hide" : "Reveal"} password</span>
              <input disabled={formDisabled} type="checkbox" class="checkbox" bind:checked={showPassword} />
            </label>
          </div>
        </div>
      </div>
      <div class="form-control mb-1 mt-6">
        <button class="btn btn-primary" type="submit" disabled={formDisabled}
          >{#if demoMode}Try Demo{:else}Login{/if}</button
        >
      </div>
      <div class="text-center text-sm">
        <a class="link-hover link link-secondary" href="https://dtcooper.github.io/tomato/" tabindex="-1"
          >Tomato Radio Automation</a
        >,
        <!-- svelte-ignore missing-declaration-->
        version:
        <span class="select-text font-mono tracking-tighter">{TOMATO_VERSION}</span>
        / protocol:
        <span class="select-text font-mono tracking-tighter">{protocolVersion}</span>
        <br />
        Copyright &copy; 2019-{dayjs().year()}
        <a class="link-hover link link-secondary" href="https://jew.pizza/" tabindex="-1">David Cooper</a>
        &amp; <a class="link-hover link link-secondary" href="https://bmir.org" tabindex="-1">BMIR</a>.<br />
        All rights reserved.
      </div>
    </form>
  </div>
</div>
