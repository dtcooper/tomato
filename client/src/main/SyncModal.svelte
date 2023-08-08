<script>
  import Icon from "../components/Icon.svelte"
  import Modal from "../components/Modal.svelte"

  import { db, syncProgress as progress } from "../stores/db"
  import { conn, logout } from "../stores/connection"
  import { prettyDatetime } from "../utils"

  import autorenew from "@iconify/icons-mdi/autorenew"
  import lanConnect from "@iconify/icons-mdi/lan-connect"
  import lanDisconnect from "@iconify/icons-mdi/lan-disconnect"

  export let show = true
  export let canDismiss = true
  export let title = `Sync status`
</script>

<Modal bind:show bind:canDismiss>
  <svelte:fragment slot="icon">
    {#if !$conn.connected}
      <Icon icon={lanDisconnect} />
    {:else if $progress.syncing}
      <Icon icon={autorenew} class="animate-[spin_2s_linear_infinite]" />
    {:else}
      <Icon icon={lanConnect} />
    {/if}
  </svelte:fragment>
  <svelte:fragment slot="title">{title}</svelte:fragment>
  <svelte:fragment slot="content">
    {#if $progress.syncing}
      <span>
        Downloading file <span class="font-mono">{$progress.current}</span>
        of <span class="font-mono">{$progress.total}</span>
      </span>
      <progress class="progress progress-primary w-full" value={$progress.percent} max="100" />
      <span class="max-w-md truncate font-mono text-sm italic">{$progress.item}</span>
    {:else if $conn.connected}
      {#if $conn.ready}
        <h2 class="text-xl italic text-success">You are fully up-to-date with the server!</h2>
      {:else}
        <h2 class="text-xl italic">Connecting...</h2>
      {/if}
    {:else}
      <h2 class="text-xl italic text-error">
        You are currently disconnected from the server. Tomato is attempting to reconnect.
      </h2>
    {/if}
    {#if $db.lastSync}
      <div>
        Last update processed: <span class="font-bold">{prettyDatetime($db.lastSync)}</span>
      </div>
    {/if}
  </svelte:fragment>
  <svelte:fragment slot="extra-buttons">
    {#if !canDismiss}
      <button type="button" class="btn btn-error" on:click|preventDefault={() => logout()} tabindex="-1"
        >Cancel &amp; Logout</button
      >
    {/if}
  </svelte:fragment>
</Modal>
