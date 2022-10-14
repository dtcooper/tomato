<script>
  import tomatoIcon from './../assets/icons/tomato.svg'
  import connectIcon from './../assets/icons/mdi-lan-connect.svg'

  let fakeProgress = 0
  let interval = null

  export let connecting = false
  export let password = ''
  export let progress = null
  export let showPassword = false
  export let error = false
  export let authError = false
  // export let progress = {percent: 50, index: 4, total: 8, filename: 'test.mp3'}

  export const submit = () => {
    connecting = true
    fakeProgress = 0
    interval = setInterval(() => {
      if (++fakeProgress > 100) {
        clearInterval(interval)
        error = "Sample connection error"
        authError = "Sample authentication error"
        connecting = false
      } else {
        progress = {percent: fakeProgress, index: fakeProgress, total: 100, filename: `test_${fakeProgress}.mp3`}
      }
    }, 15)
  }
</script>

<div class="flex flex-col justify-center items-center min-h-screen w-full max-w-screen-sm mx-auto space-y-3">
  <div class="flex w-full items-center justify-evenly">
    <div class="tomato-svg">{@html tomatoIcon}</div>
    <div class="flex flex-col items-center font-mono font-bold space-y-1">
      <h1 class="text-4xl shadow-xl">Tomato</h1>
      <h2 class="text-2xl italic">Radio Automation</h2>
    </div>
    <div class="tomato-svg">{@html tomatoIcon}</div>
  </div>
  <div class="card w-full bg-base-200 shadow-2xl relative">
    {#if connecting}
      <div
        class="absolute inset-0 flex justify-center items-center text-success"
        class:flex-col={progress}
        class:space-y-2={progress}
      >
        {#if progress}
          <div class="radial-progress" style="--value: {progress.percent}">{Math.round(progress.percent)}%</div>
        {:else}
          <span class="connect-svg">{@html connectIcon}</span>
        {/if}
        <h2 class="text-3xl italic">Logging in...</h2>
        {#if progress}
          <span x-show="progress">File {progress.index} of {progress.total}</span>
          <span class="font-mono text-sm max-w-md truncate">{progress.filename}</span>
        {/if}
      </div>
    {/if}
    <form class="card-body" class:invisible={connecting} on:submit|preventDefault={submit}>
      <div class="form-control">
        <div class="label">
          <span class="label-text">Server Address</span>
          {#if error}
            <span class="label-text-alt font-bold text-error">{error}</span>
          {/if}
        </div>
        <input
          class="input input-bordered"
          class:input-error={error}
          on:input={() => error = false}
          placeholder="https://example.org"
          type="text"
        >
      </div>
      <div class="flex gap-2">
        <div class="form-control w-full">
          <div class="label">
            <span class="label-text">Username</span>
          </div>
          <input
            class="input input-bordered"
            class:input-error={authError}
            type="text"
            placeholder="Enter username..."
            on:input={() => authError = false}
          >
          {#if authError}
            <div class="label">
              <span class="label-text-alt font-bold text-error">{authError}</span>
            </div>
          {/if}
        </div>
        <div class="form-control w-full" x-title="password">
          <div class="label">
            <span class="label-text">Password</span>
          </div>
          {#if showPassword}
            <input
              bind:value={password}
              class:input-error={authError}
              class="input input-bordered"
              on:input={() => authError = false}
              placeholder="Enter password..."
              type="text"
              autocapitalize="none"
              autocomplete="off"
              autocorrect="off"
            >
          {:else}
            <input
              bind:value={password}
              class:input-error={authError}
              class:tracking-wider={!showPassword && password.length > 0}
              class="input input-bordered"
              on:input={() => authError = false}
              placeholder="Enter password..."
              type="password"
              autocapitalize="none"
              autocomplete="off"
              autocorrect="off"
            >
          {/if}
          <div class="form-control items-end">
            <label class="label cursor-pointer space-x-3 pr-0">
              <span class="label-text">{showPassword ? 'Hide' : 'Reveal'} password</span>
              <input type="checkbox" class="checkbox" bind:checked={showPassword}>
            </label>
          </div>
        </div>
      </div>
      <div class="form-control mt-6">
        <button
          class="btn btn-primary"
          type="submit"
        >Login</button>
      </div>
    </form>
  </div>
</div>

<style lang="postcss">
  .tomato-svg > :global(svg) {
    @apply w-20 h-20;
  }
  .connect-svg > :global(svg) {
    @apply h-10 w-10 mr-1.5;
  }
</style>
