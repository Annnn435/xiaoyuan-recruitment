import { configureStore } from '@reduxjs/toolkit';

// 这里只是创建一个基本的store，实际项目中需要添加reducers
const store = configureStore({
  reducer: {
    // 这里可以添加各种reducer
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;