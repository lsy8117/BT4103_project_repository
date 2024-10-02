<template>
  <div class="main-view">
    <!-- Display the chat history at the top -->
    <div
      v-if="chatHistory.length"
      class="chat-history"
      ref="chatHistoryContainer"
    >
      <div
        v-for="(entry, index) in chatHistory"
        :key="index"
        class="response-entry"
      >
        <!-- User Query (Right) -->
        <div v-if="entry.query" class="user-query">
          <p>{{ entry.query }}</p>
        </div>

        <!-- Response (Left) -->
        <div v-if="entry.response" class="response">
          <p>{{ entry.response }}</p>
          <!-- Like/Dislike buttons -->
          <div class="feedback-buttons">
            <button @click="handleFeedback(index, 'like')">
              <font-awesome-icon :icon="['fas', 'thumbs-up']" />
            </button>
            <span v-if="entry.feedback === 'like'" class="liked">
              You liked this response
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Pre-built Prompts Section -->
    <div class="prebuilt-prompts">
      <button
        @click="handlePrebuiltPrompt('Generate my quarterly earnings in FY24')"
      >
        Generate my quarterly earnings in FY24
      </button>
      <button
        @click="
          handlePrebuiltPrompt(
            'Provide a breakdown of operating expenses for the latest quarter'
          )
        "
      >
        Provide a breakdown of operating expenses for the latest quarter
      </button>
      <button
        @click="
          handlePrebuiltPrompt(
            'List the top-performing revenue streams in FY24'
          )
        "
      >
        List the top-performing revenue streams in FY24
      </button>
      <button
        @click="
          handlePrebuiltPrompt(
            'Show a breakdown of administrative expenses for FY24'
          )
        "
      >
        Show a breakdown of administrative expenses for FY24
      </button>
    </div>

    <!-- Form to take user input -->
    <form @submit.prevent="handleSubmit" class="textarea-container">
      <div class="custom-textarea">
        <textarea
          v-model="userPrompt"
          id="prompt"
          placeholder="Enter your query here"
          class="input-area"
        ></textarea>
        <div class="input-container">
          <!-- Display chosen file and an "X" to remove it -->
          <div class="file-input-container">
            <div v-if="uploadedFile" class="file-display">
              <div class="file-item">
                <span>{{ uploadedFile.name }}</span>
                <button
                  type="button"
                  @click="removeFile"
                  class="remove-file-button"
                >
                  X
                </button>
              </div>
            </div>
            <!-- File upload for PDF attachments -->
            <input
              type="file"
              @change="handleFileUpload"
              accept="application/pdf"
              class="file-input"
            />
          </div>
          <button type="submit" class="submit-button">Submit</button>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import { library } from "@fortawesome/fontawesome-svg-core";
import { faThumbsUp, faThumbsDown } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import axios from "axios";

library.add(faThumbsUp, faThumbsDown);

export default {
  components: {
    FontAwesomeIcon,
  },
  data() {
    return {
      userPrompt: "", // to store user input or pre-built prompt
      chatHistory: [], // to store chat history with queries and responses
      uploadedFile: null, // to store the single uploaded file
    };
  },
  methods: {
    handlePrebuiltPrompt(prompt) {
      this.userPrompt = prompt;
      this.handleSubmit(); // Automatically submit the pre-built query
    },
    async handleSubmit() {
      if (this.userPrompt.trim() === "") {
        alert("Please enter a valid query.");
        return;
      }

      // Handle file along with the user query (if any file is uploaded)
      const formData = new FormData();
      formData.append("query", this.userPrompt); // Sending the query

      try {
        // Sending the text to the Flask backend
        const anonymizerResponse = await axios.post(
          "http://127.0.0.1:5000/mainpipeline",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        // Extract the anonymized text from the response
        const anonymizedQuery = anonymizerResponse.data.anonymized_query; // Change this according to output desired.

        // Add the query and the anonymized response to the chat history
        this.chatHistory.push({
          query: this.userPrompt,
          response: anonymizedQuery, // Display the anonymized text
          feedback: null, // Feedback will be either 'like' or 'dislike'
        });

        // Clear the userPrompt and the uploaded file for the next query
        this.userPrompt = "";

        // Ensure the chat scrolls to the bottom
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      } catch (error) {
        console.error("There was an error anonymizing the data:", error);
      }
    },
    handleFeedback(index, feedback) {
      this.chatHistory[index].feedback = feedback;
    },
    scrollToBottom() {
      const container = this.$refs.chatHistoryContainer;
      container.scrollTop = container.scrollHeight;
    },
    async handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        if (file.type === "application/pdf") {
          // Prepare the form data
          const formData = new FormData();
          formData.append("file", file);

          this.chatHistory.push({
            query: "Uploading file. Please wait.",
          });

          try {
            // Send the file to the Flask backend
            const uploadResponse = await axios.post(
              "http://127.0.0.1:5000/upload",
              formData,
              {
                headers: {
                  "Content-Type": "multipart/form-data",
                },
              }
            );

            // Update the uploadedFile to display it in the UI
            this.uploadedFile = file;

            // Add the query and the anonymized response to the chat history
            this.chatHistory.push({
              response: uploadResponse.data.message,
            });
          } catch (error) {
            console.error("Error uploading file:", error);
            alert("There was an error uploading the file.");
          }
        } else {
          alert("Please upload a valid PDF file.");
        }
      }
      event.target.value = ""; // Reset the file input to allow the same file to be reselected
    },
    async removeFile() {
      this.uploadedFile = null;

      try {
        // Send request to backend to clear the anonymized text
        await axios.post("http://127.0.0.1:5000/clear_anonymized_text");
        console.log("Anonymized text cleared on the backend.");
      } catch (error) {
        console.error("Error clearing anonymized file text:", error);
      }

      this.chatHistory.push({
        query: "File removed.",
      });
    },
  },
};
</script>

<style scoped>
.main-view {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100vh;
  width: 95%;
  margin: 0 auto;
}

/* Chat history section */
.chat-history {
  flex-grow: 1;
  margin-bottom: 20px;
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 10px;
}

.response-entry {
  display: flex;
  flex-direction: column;
}

.user-query {
  align-self: flex-end;
  background-color: rgb(246, 229, 209);
  padding: 0px 20px;
  margin: 10px 0px;
  font-family: "Montserrat", sans-serif;
  border-radius: 10px;
  max-width: 60%;
  display: flex;
  word-wrap: break-word;
  text-align: right;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.response {
  align-self: flex-start;
  background-color: #f1f1f1;
  padding: 0px 20px;
  margin: 10px 0px;
  border-radius: 10px;
  font-family: "Montserrat", sans-serif;
  max-width: 60%;
  display: inline-block;
  word-wrap: break-word;
  text-align: left;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

/* Feedback buttons */
.feedback-buttons {
  margin-top: 10px;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.feedback-buttons button {
  margin-right: 10px;
  margin-bottom: 10px;
  padding: 5px 10px;
  font-size: 0.9em;
  font-family: "Montserrat", sans-serif;
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

/* Prebuilt Prompts Styling */
.prebuilt-prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-bottom: 0px;
  gap: 10px;
}

.prebuilt-prompts button {
  flex: 0 1 calc(50% - 10px);
  padding: 10px 20px;
  margin: 2px;
  font-size: 1em;
  font-family: "Montserrat", sans-serif;
  background-color: rgb(205, 170, 128);
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
.textarea-container {
  position: relative;
  display: flex;
  width: 100%;
}

.custom-textarea {
  width: 100%;
  padding: 15px;
  border-radius: 10px;
  border: 1px solid #ccc;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  background-color: #f9f9f9;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
}

.input-area {
  width: 100%;
  min-height: 50px;
  padding: 10px;
  border: none;
  font-family: "Montserrat", sans-serif;
  font-size: 1em;
  box-sizing: border-box;
  margin-bottom: 10px;
}

.input-container {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
}

.file-input-container {
  display: flex;
  flex-direction: column;
}

.file-display {
  display: flex;
  flex-direction: column;
  margin-bottom: 5px;
}

.file-item {
  display: flex;
  align-items: center;
}

.file-item span {
  margin-right: 10px;
  font-size: small;
}

.remove-file-button {
  background: red;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.remove-file-button:hover {
  background: darkred;
}

.file-input {
  margin-bottom: 5px;
}

.submit-button {
  padding: 10px;
  font-size: 0.9em;
  height: 3em;
  font-family: "Montserrat", sans-serif;
  background-color: bisque;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  align-self: flex-end;
}

.submit-button:hover {
  background-color: rgb(237, 179, 107);
}

.feedback-buttons {
  margin-top: 10px;
}

.feedback-buttons button {
  margin-right: 10px;
  margin-bottom: 10px;
  padding: 5px 10px;
  font-size: 0.9em;
  font-family: "Montserrat", sans-serif;
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
