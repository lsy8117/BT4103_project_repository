<template>
  <div class="main-view">
    <!-- Display the chat history at the top -->
    <div v-if="chatHistory.length" class="chat-history" ref="chatHistoryContainer">
      <div v-for="(entry, index) in chatHistory" :key="index" class="response-entry">
        <!-- User Query (Right) -->
        <div class="user-query">
          <p>{{ entry.query }}</p>
        </div>
        
        <!-- Response (Left) -->
        <div class="response">
          <p>{{ entry.response }}</p>
          <!-- Like/Dislike buttons -->
          <div class="feedback-buttons">
            <button @click="handleFeedback(index, 'like')">
              <font-awesome-icon :icon="['fas', 'thumbs-up']" />
            </button>
            <button @click="handleFeedback(index, 'dislike')">
              <font-awesome-icon :icon="['fas', 'thumbs-down']" />
            </button>
            <span v-if="entry.feedback" :class="entry.feedback === 'like' ? 'liked' : 'disliked'">
              {{ entry.feedback === 'like' ? 'You liked this response' : 'You disliked this response' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Pre-built Prompts Section -->
    <div class="prebuilt-prompts">
      <button @click="handlePrebuiltPrompt('Generate my quarterly earnings in FY24')">
        Generate my quarterly earnings in FY24
      </button>
      <button @click="handlePrebuiltPrompt('Provide a breakdown of operating expenses for the latest quarter')">
        Provide a breakdown of operating expenses for the latest quarter
      </button>
      <button @click="handlePrebuiltPrompt('List the top-performing revenue streams in FY24')">
        List the top-performing revenue streams in FY24
      </button>
      <button @click="handlePrebuiltPrompt('Show a breakdown of administrative expenses for FY24')">
        Show a breakdown of administrative expenses for FY24
      </button>
    </div>

    <!-- Form to take user input -->
    <form @submit.prevent="handleSubmit" class="textarea-container">
      <textarea v-model="userPrompt" id="prompt" placeholder="Enter your query here"></textarea>
      <button type="submit" class="submit-button">Submit</button>
    </form>

  </div>
</template>

<script>
import { library } from '@fortawesome/fontawesome-svg-core';
import { faThumbsUp, faThumbsDown } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

library.add(faThumbsUp, faThumbsDown);

export default {
  components: {
    FontAwesomeIcon,
  },
  data() {
    return {
      userPrompt: '', // to store user input or pre-built prompt
      chatHistory: [], // to store chat history with queries and responses
    };
  },
  methods: {
    // When a pre-built prompt is clicked, set it and automatically submit
    handlePrebuiltPrompt(prompt) {
      this.userPrompt = prompt;
      this.handleSubmit();    // Automatically submit the pre-built query
    },
    handleSubmit() {
      if (this.userPrompt.trim() === '') {
        alert('Please enter a valid query.');
        return;
      }

      // Simulate a response (replace this with actual API call later)
      const simulatedResponse = `This is a placeholder response for: "${this.userPrompt}"`;

      // Add the query and response to the chat history
      this.chatHistory.push({
        query: this.userPrompt,
        response: simulatedResponse,
        feedback: null, // Feedback will be either 'like' or 'dislike'
      });

      // Clear the userPrompt for the next query
      this.userPrompt = '';

      // Ensure the chat scrolls to the bottom
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    handleFeedback(index, feedback) {
      this.chatHistory[index].feedback = feedback;
    },
    scrollToBottom() {
      const container = this.$refs.chatHistoryContainer;
      container.scrollTop = container.scrollHeight;
    },
  },
};
</script>

<style scoped>
.main-view {
  display: flex;
  flex-direction: column;
  justify-content: flex-end; /* Align content to the bottom */
  height: 100vh;
  width: 95%;
  margin: 0 auto;
}

/* Chat history section */
.chat-history {
  flex-grow: 1;
  margin-bottom: 20px;
  max-height: 400px; /* Set a max height for the chat history block */
  overflow-y: auto; /* Allows scrolling if chat history exceeds max height */
  display: flex;
  flex-direction: column; /* Regular column direction */
  justify-content: flex-start;
  padding: 10px;
}

.response-entry {
  display: flex;
  flex-direction: column
}

/* Style for the user's query (aligned right) */
.user-query {
  align-self: flex-end; /* Align to the right */
  background-color:rgb(246, 229, 209);
  padding: 0px 20px;
  margin: 10px 0px;
  font-family: 'Montserrat', sans-serif;
  border-radius: 10px;
  max-width: 60%; /* Set a max width for the query bubble */
  display: flex; /* Allow bubble to wrap the text naturally */
  word-wrap: break-word; /* Handle long words */
  text-align: right;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

/* Style for the response (aligned left) */
.response {
  align-self: flex-start; /* Align to the left */
  background-color: #f1f1f1; /* Light grey background */
  padding: 0px 20px;
  margin: 10px 0px;
  border-radius: 10px;
  font-family: 'Montserrat', sans-serif;
  max-width: 60%; /* Set a max width for the response bubble */
  display: inline-block; /* Allow bubble to wrap the text naturally */
  word-wrap: break-word; /* Handle long words */
  text-align: left;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.liked, .disliked {
  font-weight:lighter;
  font-style: italic;
  font-size: 0.7em;
  font-family: 'Montserrat', sans-serif;
  margin-bottom: 5px;
  display: block; /* This ensures it displays on its own line */
}

/* Prebuilt Prompts Styling */
.prebuilt-prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-bottom: 40px;
  gap: 10px;
}

.prebuilt-prompts button {
  flex: 0 1 calc(50% - 10px); /* Ensure two buttons per row with some gap */
  padding: 10px 20px;
  margin: 2px;
  font-size: 1em;
  font-family: 'Montserrat', sans-serif;
  background-color:rgb(205, 170, 128);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  height: 3em;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.prebuilt-prompts button:hover {
  background-color: rgb(193, 138, 70);
}

/* Form Styling */
form {
  display: flex;
  flex-direction: column; /* Stack elements vertically */
  width: 100%;
  margin: 0 auto; /* Center the form */
}

.textarea-container {
  position: relative;
  display: flex;
  align-items: flex-end; /* Align the button to the right */
  width: 100%;
}

textarea {
  width: 100%;
  padding: 20px;
  border-radius: 10px;
  border: none;
  font-size: 1em;
  font-family: 'Montserrat', sans-serif;
  height: 100px;
  box-sizing: border-box;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.submit-button {
  padding: 10px 10px; /* Controls the size of the button */
  margin-right: 10px;
  transform: translateY(-130%);
  font-size: 0.9em;
  font-family: 'Montserrat', sans-serif;
  background-color: bisque;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  text-align: center; /* Ensures text is centered */
}

.submit-button:hover {
  background-color:rgb(237, 179, 107);
}

.feedback-buttons {
  margin-top: 10px;
}

.feedback-buttons button {
  margin-right: 10px;
  margin-bottom: 10px;
  padding: 5px 10px;
  font-size: 0.9em;
  font-family: 'Montserrat', sans-serif;
  background-color: white;
  border-width: 0.2px;
  border-radius: 4px;
  border-color: black;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.feedback-buttons button:hover {
  background-color: rgb(224, 246, 255);
}
</style>
