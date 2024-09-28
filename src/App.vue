<template>
  <div id="app">
    <HomeView/>
  </div>
</template>

<script>
import HomeView from './views/HomeView.vue';

export default {
  name: 'App',
  components: {
    HomeView
  }
};
</script>

<style>
#app {
  display: flex;
  flex-direction: column; /* Stack items vertically */
  justify-content: center; /* Center items vertically */
  align-items: center; /* Center items horizontally */
  width: 100%;
  height: 100vh; /* Make sure the container fills the full viewport height */
  background-color:rgb(238, 232, 224);
  padding-top: 10px;
  padding-bottom: 10px;
  box-sizing: border-box; /* Ensure padding doesn't affect the height */
  margin: 0;
  overflow: hidden; /* Prevent any scrolling */
}

body {
  margin: 0;
  padding: 0;
  height: 100vh; /* Ensure the body takes up full viewport height */
  overflow: hidden; /* Prevent body scrolling */
}
</style>
