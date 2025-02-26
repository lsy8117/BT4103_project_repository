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
          <!-- Display the model used for this response -->
          <p style="margin: 2% 0 0 0">[{{ entry.model }}]</p>
          <p style="margin: 3% 0 0 0">{{ entry.response }}</p>
          <!-- Like/Dislike buttons -->
          <div class="feedback-buttons">
            <button
              :class="{ 'button-liked': entry.feedback === 'like' }"
              @click="handleFeedback(index)"
            >
              <font-awesome-icon :icon="['fas', 'thumbs-up']" />
            </button>
            <span v-if="entry.feedback === 'like'" class="liked">
              <i>You liked this response</i>
            </span>
          </div>
          <!-- Conditional Component based on query value -->
          <div
            v-if="
              (entry.model === 'Vectordb' ||
                entry.model === 'Finetuned Phi3.5 mini') &&
              index === chatHistory.length - 1
            "
          >
            <button
              @click="handleIrrelevantOutput(index)"
              class="relevancy-check"
            >
              Not relevant?
            </button>
            <span v-if="isRegenerating" class="liked">
              <i>Regenerating response...</i>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Pre-built Prompts Section -->
    <div class="restart-container">
      <b-button class="restart" @click="restartConversation">
        <span v-if="isClearing">
          <i class="fa fa-spinner fa-spin"></i> Processing...
        </span>
        <span v-else>Restart Conversation</span>
      </b-button>
    </div>

    <!-- Pre-built Prompts Section -->
    <div class="prebuilt-prompts">
      <button @click="handlePrebuiltPrompt(this.query_1)">
        {{ query_1 }}
      </button>
      <button @click="handlePrebuiltPrompt(this.query_2)">
        {{ query_2 }}
      </button>
      <button @click="handlePrebuiltPrompt(this.query_3)">
        {{ query_3 }}
      </button>
      <button @click="handlePrebuiltPrompt(this.query_4)">
        {{ query_4 }}
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
            <div
              v-for="file in uploadedFiles"
              :key="file.name"
              class="file-display"
            >
              <div class="file-item">
                <span>{{ file.name }}</span>
                <button
                  type="button"
                  @click="removeFile(file)"
                  class="remove-file-button"
                  v-if="!isRemovingFile"
                >
                  X
                </button>
                <div v-else class="spinner"></div>
              </div>
            </div>
            <!-- File upload for PDF attachments -->
            <input
              type="file"
              ref="fileInput"
              @change="handleFileUpload"
              multiple
              accept="application/pdf,text/csv,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              class="file-input"
              :disabled="isUploading"
            />
            <div v-if="isUploading" class="spinner"></div>
          </div>
          <template v-if="!isSubmitting">
            <button type="submit" class="submit-button" :disabled="isUploading">
              Submit
            </button>
          </template>
          <template v-else>
            <div class="spinner"></div>
            <!-- Spinner for submit button -->
          </template>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import { library } from '@fortawesome/fontawesome-svg-core'
import { faThumbsUp, faThumbsDown } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import axios from 'axios'

library.add(faThumbsUp, faThumbsDown)

export default {
  components: {
    FontAwesomeIcon,
  },
  data() {
    return {
      userPrompt: '', // to store user input or pre-built prompt
      chatHistory: [], // to store chat history with queries and responses
      uploadedFiles: [], // to store the uploaded files
      model: '',
      isSubmitting: false, // Track loading state for submit button
      isUploading: false,
      isRemovingFile: false,
      isRegenerating: false,
      isClearing: false,
      query_1: null,
      query_2: null,
      query_3: null,
      query_4: null,
    }
  },

  methods: {
    handlePrebuiltPrompt(prompt) {
      this.userPrompt = prompt
      this.handleSubmit() // Automatically submit the pre-built query
    },

    async getRecentConvo() {
      try {
        const response = await axios.post(
          'http://127.0.0.1:5000/get_recent_queries'
        )
        console.log(response)
        this.query_1 = response.data.query_1
        this.query_2 = response.data.query_2
        this.query_3 = response.data.query_3
        this.query_4 = response.data.query_4
      } catch (error) {
        console.error('Error retrieving recent queries in VectorDB: ', error)
      }
    },

    async restartConversation() {
      ;(this.isClearing = true), (this.chatHistory = [])

      try {
        const response = await axios.post(
          'http://127.0.0.1:5000/clear_chat_history'
        )
        console.log(response)
      } catch (error) {
        console.error('Error clearing chat history: ', error)
      } finally {
        this.isClearing = false
      }
    },

    async handleSubmit() {
      if (this.userPrompt.trim() === '') {
        alert('Please enter a valid query.')
        return
      }

      this.isSubmitting = true

      // Handle file along with the user query (if any file is uploaded)
      const formData = new FormData()
      formData.append('query', this.userPrompt) // Sending the query

      try {
        // Sending the text to the Flask backend
        const anonymizerResponse = await axios.post(
          'http://127.0.0.1:5000/mainpipeline',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        )

        this.handleOutput(anonymizerResponse)

        // Clear the userPrompt for the next query
        this.userPrompt = ''

        // Ensure the chat scrolls to the bottom
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (error) {
        console.error('There was an error in getting response:', error)
      } finally {
        this.isSubmitting = false
      }
    },

    async handleFeedback(index) {
      if (this.chatHistory[index].model === 'Vectordb') {
        alert('Cannot save similar queries')
        return
      } else if (
        this.chatHistory.length !== 1 ||
        this.uploadedFiles.length !== 0
      ) {
        alert('Cannot save contextual query')
        return
      } else {
        if (this.chatHistory[index].feedback === 'like') {
          this.chatHistory[index].feedback = null // Toggle to remove like
        } else {
          this.chatHistory[index].feedback = 'like' // Set like
        }

        const answer =
          this.chatHistory[index].feedback === 'like'
            ? this.chatHistory[index].response
            : null

        try {
          const response = await axios.post(
            'http://127.0.0.1:5000/handle_feedback',
            {
              query: this.chatHistory[index].query,
              answer: answer,
            }
          )
          if (answer != null) {
            console.log('Uploaded to VectorDB')
          } else {
            console.log('Removed from VectorDB')
          }
        } catch (error) {
          console.error('Error saving query-answer to vectordb:', error)
        }
      }
    },

    handleOutput(anonymizerResponse) {
      // Extract the anonymized query, gemini output, and deanonymized output from the response
      const originalQuery = anonymizerResponse.data.original_query
      const anonymizedQuery = anonymizerResponse.data.anonymized_query
      const anonymizedContext = anonymizerResponse.data.anonymized_context
      const geminiOutput = anonymizerResponse.data.gemini_output
      const deanonymizedOutput =
        anonymizerResponse.data.deanonymized_output.trimStart()
      const model = anonymizerResponse.data.model_used

      // Log anonymized query and gemini output to the console
      console.log('Anonymized Query:', anonymizedQuery)
      console.log('Anonymized Context:', anonymizedContext)
      console.log('Gemini Output:', geminiOutput)
      console.log('Deanonymized Output: ', deanonymizedOutput)
      console.log('Model used: ', model)

      // Add the deanonymized output to the chat history
      this.chatHistory.push({
        model: model,
        query: originalQuery,
        response: deanonymizedOutput, // Only display the deanonymized output
        feedback: null, // Feedback will be either 'like' or 'dislike'
      })
    },

    handleIrrelevantOutput(index) {
      this.isRegenerating = true
      this.regeneratingOutput(index)
    },

    async regeneratingOutput(index) {
      // regenerate answer from backend
      this.isSubmitting = true

      const formData = new FormData()
      formData.append('query', this.chatHistory[index].query)
      formData.append('origin', this.chatHistory[index].model)

      try {
        const anonymizerResponse = await axios.post(
          'http://127.0.0.1:5000/reprocessquery',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        )

        this.handleOutput(anonymizerResponse)

        // Clear the userPrompt for the next query
        this.userPrompt = ''

        this.chatHistory.splice(index, 1)
        this.isRegenerating = false
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (error) {
        console.error('There was an error in getting response:', error)
      } finally {
        this.isSubmitting = false
      }
    },

    scrollToBottom() {
      const container = this.$refs.chatHistoryContainer
      container.scrollTop = container.scrollHeight
    },

    async handleFileUpload(event) {
      const newFiles = Array.from(event.target.files).filter(
        (f) =>
          this.uploadedFiles.map((file) => file.name).indexOf(f.name) === -1
      )

      if (newFiles.length > 0) {
        this.isUploading = true
        const uploadFilePromises = newFiles.map(async (file) => {
          const allowedTypes = [
            'application/pdf',
            'text/csv',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          ]

          if (allowedTypes.includes(file.type)) {
            // Prepare the form data
            const formData = new FormData()
            formData.append('file', file)

            try {
              // Send the file to the Flask backend
              const uploadResponse = await axios.post(
                'http://127.0.0.1:5000/upload',
                formData,
                {
                  headers: {
                    'Content-Type': 'multipart/form-data',
                  },
                }
              )
              this.uploadedFiles.push(file)
            } catch (error) {
              console.error('Error uploading file:', error)
              alert('There was an error uploading the file.')
            }
          } else {
            alert('Please upload a valid PDF, CSV, or DOCX file.')
          }
        })

        Promise.all(uploadFilePromises).then(() => {
          this.isUploading = false
        })
      }
    },

    async removeFile(fileToRemove) {
      this.isRemovingFile = true
      try {
        // Send request to backend to clear the anonymized text
        const removeResponse = await axios.post(
          'http://127.0.0.1:5000/clear_anonymized_text',
          {
            fileName: fileToRemove.name,
          }
        )
        console.log('Anonymized text for the file cleared on the backend.')
        this.uploadedFiles = this.uploadedFiles.filter(
          (file) => file !== fileToRemove
        )
      } catch (error) {
        console.error('Error clearing anonymized file text:', error)
      } finally {
        this.isRemovingFile = false
      }
      // Reset the input element to allow re-uploading the same file
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
  },

  mounted() {
    this.getRecentConvo()
  },
}
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
  /* max-height: 400px; */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 10px;
}

.response-entry {
  display: flex;
  flex-direction: column;
  white-space: pre-wrap;
}

.restart-container {
  display: flex;
  justify-content: flex-end; /* Aligns children to the right */
  align-items: center; /* Centers children vertically */
  width: 100%;
  padding: 5px 0;
}

.restart {
  background-color: initial;
  background-image: linear-gradient(-180deg, #ff7e31, #e62c03);
  border-radius: 6px;
  box-shadow: rgba(0, 0, 0, 0.1) 0 2px 4px;
  color: #ffffff;
  cursor: pointer;
  display: inline-block;
  font-family: Inter, -apple-system, system-ui, Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  height: 40px;
  line-height: 40px;
  outline: 0;
  overflow: hidden;
  padding: 0 20px;
  pointer-events: auto;
  position: relative;
  text-align: center;
  touch-action: manipulation;
  user-select: none;
  -webkit-user-select: none;
  vertical-align: top;
  white-space: nowrap;
  width: 15%;
  z-index: 9;
  border: 0;
  transition: box-shadow 0.2s;
}

.restart:hover {
  box-shadow: rgba(253, 76, 0, 0.5) 0 3px 8px;
}

.user-query {
  align-self: flex-end;
  background-color: rgb(246, 229, 209);
  padding: 0px 20px;
  margin: 10px 0px;
  font-family: 'Montserrat', sans-serif;
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
  padding: 10px 20px;
  margin: 10px 0px 10px;
  border-radius: 10px;
  font-family: 'Montserrat', sans-serif;
  max-width: 60%;
  display: inline-block;
  word-wrap: break-word;
  text-align: left;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

/* Feedback buttons */
.feedback-buttons {
  margin-top: 10px;
  margin-bottom: 10px;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.feedback-buttons button {
  margin-right: 10px;
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

.liked {
  font-style: italic;
  font-size: small;
}

.button-liked {
  background-color: rgb(194, 229, 242) !important;
  border: none;
}

.relevancy-check {
  background-color: #fff;
  border: 1px solid #d5d9d9;
  border-radius: 8px;
  box-shadow: rgba(213, 217, 217, 0.5) 0 2px 5px 0;
  box-sizing: border-box;
  color: #0f1111;
  cursor: pointer;
  display: inline-block;
  font-family: 'Amazon Ember', sans-serif;
  font-size: 12px;
  line-height: 29px;
  padding: 0 10px 0 11px;
  position: relative;
  text-align: center;
  text-decoration: none;
  user-select: none;
  -webkit-user-select: none;
  touch-action: manipulation;
  vertical-align: middle;
  width: 100px;
}

.relevancy-check:hover {
  background-color: #f7fafa;
}

.relevancy-check:focus {
  border-color: #008296;
  box-shadow: rgba(213, 217, 217, 0.5) 0 2px 5px 0;
  outline: 0;
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
  font-family: 'Montserrat', sans-serif;
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
  font-family: 'Montserrat', sans-serif;
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
  font-family: 'Montserrat', sans-serif;
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

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #de9534;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
