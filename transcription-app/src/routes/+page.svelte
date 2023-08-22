<script>
	import { onMount } from 'svelte';
	import { v4 } from 'uuid';
	import { env } from '$env/dynamic/public';

	let audioChunks = []; // Store audio data chunks
	let mediaRecorder = null;
	// let recording = false
	let uid = null;
	// let intervalTimer = null;
	let audioElement = null;
	let socket;
	let transcript;

	$: console.log('Transcript: ', transcript);
	/**
	 * Resamples the audio data to a target sample rate of 16kHz.
	 * @param {Array|ArrayBuffer|TypedArray} audioData - The input audio data.
	 * @param {number} [origSampleRate=44100] - The original sample rate of the audio data.
	 * @returns {Float32Array} The resampled audio data at 16kHz.
	 */
	function resampleTo16kHZ(audioData, origSampleRate = 44100) {
		// Convert the audio data to a Float32Array
		const data = new Float32Array(audioData);

		// Calculate the desired length of the resampled data
		const targetLength = Math.round(data.length * (16000 / origSampleRate));

		// Create a new Float32Array for the resampled data
		const resampledData = new Float32Array(targetLength);

		// Calculate the spring factor and initialize the first and last values
		const springFactor = (data.length - 1) / (targetLength - 1);
		resampledData[0] = data[0];
		resampledData[targetLength - 1] = data[data.length - 1];

		// Resample the audio data
		for (let i = 1; i < targetLength - 1; i++) {
			const index = i * springFactor;
			const leftIndex = Math.floor(index).toFixed();
			const rightIndex = Math.ceil(index).toFixed();
			const fraction = index - leftIndex;
			resampledData[i] = data[leftIndex] + (data[rightIndex] - data[leftIndex]) * fraction;
		}

		// Return the resampled data
		return resampledData;
	}

	async function startRecording() {
		const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); // audio stream
		// const origSampleRate = stream.getAudioTracks()[0].getSettings().sampleRate;
		// const audioChannelCount = stream.getAudioTracks()[0].getSettings().channelCount;
		// console.log('Audio channel count: ', audioChannelCount)
		// console.log('Sample rate: ', origSampleRate)

		// mediaRecorder = new MediaRecorder(stream);
		// mediaRecorder.start(10000) // fire the dataavailable event every 1s

		uid = v4(); // generate a unique id for this recording

		if (stream) {
			// console.log('Media recorder', mediaRecorder)
			socket = new WebSocket(env.PUBLIC_WEBSOCKET_URL); // create a websocket connection
			let isServerReady = false;

			socket.onopen = (event) => {
				// when the connection is open send the handshake
				socket.send(
					JSON.stringify({
						uid: uid,
						multilingual: false,
						language: 'en',
						task: 'transcribe'
					})
				);
			};

			socket.onmessage = async (event) => {
				const data = JSON.parse(event.data);

				if (data.uid !== uid) return; // ignore messages that are not for this recording

				if (data?.message && data?.message === 'SERVER_READY') {
					console.log('Server ready');
					isServerReady = true;
					return;
				}

				if (data.message === 'DISCONNECTED') {
					console.log('Server disconnected');
					socket.close();
					return;
				}
				// console.log('Transcript: ', typeof event.data)
				transcript = JSON.parse(event.data);
			};

			const audioDataCache = [];
			const context = new AudioContext();
			const mediaStream = context.createMediaStreamSource(stream);
			const recorder = context.createScriptProcessor(4096, 1, 1);
			recorder.onaudioprocess = async (event) => {
				if (!context || !isServerReady) return;

				const inputData = event.inputBuffer.getChannelData(0);
				const audioData16kHz = resampleTo16kHZ(inputData, context.sampleRate);

				audioDataCache.push(inputData);

				socket.send(audioData16kHz);
			};

			mediaStream.connect(recorder);
			recorder.connect(context.destination);
			
      
		} else {
			if (socket) {
				socket.close();
				audioChunks = [];
			}
			return;
		}
	}

	function stopRecording() {}

	onMount(() => {
		audioElement = document.querySelector('audio');
	});
</script>

<div>
	<button on:click={startRecording}>Start</button>
	<button on:click={stopRecording}>Stop</button>
	<audio controls />
	<div class="transcript">
		{#if transcript}
			{#each transcript.segments as segment}
				<div class="timestamps">
					<p>Start: {segment.start}</p>
					<p>End: {segment.end}</p>
				</div>
				<p>{segment.text}</p>
			{/each}
		{/if}
	</div>
</div>

<style>
	.timestamps {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
	}

	.transcript {
		margin-top: 20px;
	}
</style>
