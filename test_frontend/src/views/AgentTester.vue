<template>
  <div class="agent-tester">
    <div class="page-header">
      <h2>
        <el-icon><Cpu /></el-icon>
        Agent Testing Center
      </h2>
      <p>Test all CorePlay agents with custom inputs and configurations</p>
    </div>

    <!-- Custom Prompt Indicator -->
    <el-alert
      v-if="usingCustomPrompt"
      :title="`Testing Custom Prompt: ${customPromptData?.agent_type}`"
      type="info"
      :closable="true"
      @close="usingCustomPrompt = false"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #default>
        <p>You are testing a custom prompt from the Prompt Editor. The agent will use your rewritten prompt instead of the saved version.</p>
        <div class="custom-prompt-info">
          <p><strong>System Prompt:</strong> {{ customPromptData?.system_prompt?.substring(0, 100) }}...</p>
          <p><strong>User Template:</strong> {{ customPromptData?.user_prompt_template?.substring(0, 100) }}...</p>
        </div>
      </template>
    </el-alert>

    <el-row :gutter="20">
      <!-- Agent Selection -->
      <el-col :span="6">
        <el-card class="agent-selector">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>Select Agent</span>
            </div>
          </template>
          
          <el-radio-group v-model="selectedAgent" @change="onAgentChange">
            <el-radio 
              v-for="agent in availableAgents" 
              :key="agent.type" 
              :label="agent.type"
              class="agent-radio"
            >
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-desc">{{ agent.description }}</div>
              </div>
            </el-radio>
          </el-radio-group>
        </el-card>
      </el-col>

      <!-- Input Configuration -->
      <el-col :span="10">
        <el-card class="input-config">
          <template #header>
            <div class="card-header">
              <el-icon><Edit /></el-icon>
              <span>Input Configuration</span>
            </div>
          </template>

          <!-- Agent-specific input forms -->
          <div v-if="selectedAgent === 'diary'" class="agent-form">
            <h4>Diary Agent Test</h4>
            <el-form :model="diaryInput" label-width="120px">
              <el-form-item label="Event Category">
                <el-select v-model="diaryInput.event_category" @change="onEventCategoryChange" placeholder="Select event category">
                  <el-option label="Human-Toy Interaction (Interactive Agent)" value="human_toy_interactive_function" />
                  <el-option label="Dialogue (Dialogue Agent)" value="human_toy_talk" />
                  <el-option label="Neglect (Neglect Agent)" value="unkeep_interactive" />
                  <el-option label="Trending (Trending Agent)" value="trending_events" />
                  <el-option label="Weather (Weather Agent)" value="weather_events" />
                  <el-option label="Holiday (Holiday Agent)" value="holiday_events" />
                  <el-option label="Friends (Friends Agent)" value="friends_function" />
                  <el-option label="Adoption (Adoption Agent)" value="adopted_function" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="Event Name">
                <el-select v-model="diaryInput.event_name" placeholder="Select event name">
                  <el-option 
                    v-for="eventName in availableEventNames" 
                    :key="eventName" 
                    :label="eventName" 
                    :value="eventName"
                  />
                </el-select>
              </el-form-item>

              <!-- Dynamic input fields based on event category -->
              <div v-if="diaryInput.event_category === 'human_toy_interactive_function'">
                <el-form-item label="Interaction Type">
                  <el-input v-model="diaryInput.interaction_type" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.interaction_type" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.interaction_type = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['抚摸', '拥抱', '轻拍']" 
                      :key="suggestion"
                      @click="diaryInput.interaction_type = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Duration">
                  <el-input v-model="diaryInput.duration" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.duration" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.duration = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['5分钟', '10秒', '1小时']" 
                      :key="suggestion"
                      @click="diaryInput.duration = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="User Response">
                  <el-select v-model="diaryInput.user_response" placeholder="Select response type">
                    <el-option label="Positive" value="positive" />
                    <el-option label="Negative" value="negative" />
                    <el-option label="Neutral" value="neutral" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Toy Emotion">
                  <el-input v-model="diaryInput.toy_emotion" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.toy_emotion" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.toy_emotion = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['开心', '兴奋', '满足']" 
                      :key="suggestion"
                      @click="diaryInput.toy_emotion = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'human_toy_talk'">
                <el-form-item label="Dialogue Content">
                  <el-input 
                    v-model="diaryInput.dialogue_content" 
                    type="textarea" 
                    :rows="3"
                    placeholder="输入对话内容..."
                  />
                </el-form-item>
                <el-form-item label="Emotional Tone">
                  <el-select v-model="diaryInput.emotional_tone" placeholder="Select emotional tone">
                    <el-option label="Positive" value="positive" />
                    <el-option label="Negative" value="negative" />
                    <el-option label="Neutral" value="neutral" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Topic">
                  <el-input v-model="diaryInput.topic" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.topic" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.topic = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['学习', '游戏', '生活']" 
                      :key="suggestion"
                      @click="diaryInput.topic = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'unkeep_interactive'">
                <el-form-item label="Neglect Duration">
                  <el-input v-model="diaryInput.neglect_duration" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.neglect_duration" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.neglect_duration = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['1天', '3天', '7天']" 
                      :key="suggestion"
                      @click="diaryInput.neglect_duration = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Neglect Type">
                  <el-select v-model="diaryInput.neglect_type" placeholder="Select neglect type">
                    <el-option label="No Dialogue" value="no_dialogue" />
                    <el-option label="No Interaction" value="no_interaction" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Toy Emotion">
                  <el-input v-model="diaryInput.toy_emotion" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.toy_emotion" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.toy_emotion = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['孤独', '想念', '失落']" 
                      :key="suggestion"
                      @click="diaryInput.toy_emotion = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'trending_events'">
                <el-form-item label="Trend Type">
                  <el-select v-model="diaryInput.trend_type" placeholder="Select trend type">
                    <el-option label="Celebration" value="celebration" />
                    <el-option label="Disaster" value="disaster" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Trend Topic">
                  <el-input v-model="diaryInput.trend_topic" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.trend_topic" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.trend_topic = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['节日庆祝', '自然灾害', '科技新闻']" 
                      :key="suggestion"
                      @click="diaryInput.trend_topic = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Social Sentiment">
                  <el-input v-model="diaryInput.social_sentiment" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.social_sentiment" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.social_sentiment = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['积极', '消极', '中性']" 
                      :key="suggestion"
                      @click="diaryInput.social_sentiment = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'weather_events'">
                <el-form-item label="Weather Type">
                  <el-input v-model="diaryInput.weather_type" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.weather_type" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.weather_type = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['晴天', '雨天', '雪天']" 
                      :key="suggestion"
                      @click="diaryInput.weather_type = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Temperature">
                  <el-input v-model="diaryInput.temperature" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.temperature" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.temperature = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['25°C', '寒冷', '炎热']" 
                      :key="suggestion"
                      @click="diaryInput.temperature = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Preference">
                  <el-select v-model="diaryInput.preference" placeholder="Select preference">
                    <el-option label="Favorite" value="favorite" />
                    <el-option label="Dislike" value="dislike" />
                  </el-select>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'holiday_events'">
                <el-form-item label="Holiday Name">
                  <el-input v-model="diaryInput.holiday_name" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.holiday_name" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.holiday_name = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['春节', '中秋节', '国庆节']" 
                      :key="suggestion"
                      @click="diaryInput.holiday_name = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Holiday Phase">
                  <el-select v-model="diaryInput.holiday_phase" placeholder="Select holiday phase">
                    <el-option label="Approaching" value="approaching" />
                    <el-option label="During" value="during" />
                    <el-option label="Ends" value="ends" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Celebration Activity">
                  <el-input v-model="diaryInput.celebration_activity" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.celebration_activity" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.celebration_activity = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['放烟花', '吃月饼', '旅行']" 
                      :key="suggestion"
                      @click="diaryInput.celebration_activity = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'friends_function'">
                <el-form-item label="Friend Action">
                  <el-select v-model="diaryInput.friend_action" placeholder="Select friend action">
                    <el-option label="Made New Friend" value="made_new_friend" />
                    <el-option label="Friend Deleted" value="friend_deleted" />
                    <el-option label="Liked Single" value="liked_single" />
                    <el-option label="Liked 3-5" value="liked_3_to_5" />
                    <el-option label="Liked 5+" value="liked_5_plus" />
                    <el-option label="Disliked Single" value="disliked_single" />
                    <el-option label="Disliked 3-5" value="disliked_3_to_5" />
                    <el-option label="Disliked 5+" value="disliked_5_plus" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Friend Name">
                  <el-input v-model="diaryInput.friend_name" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.friend_name" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.friend_name = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['小明', '小红', '小刚']" 
                      :key="suggestion"
                      @click="diaryInput.friend_name = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Social Context">
                  <el-input v-model="diaryInput.social_context" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.social_context" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.social_context = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['学校', '工作', '网络']" 
                      :key="suggestion"
                      @click="diaryInput.social_context = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <div v-else-if="diaryInput.event_category === 'adopted_function'">
                <el-form-item label="Adoption Status">
                  <el-select v-model="diaryInput.adoption_status" placeholder="Select adoption status">
                    <el-option label="Toy Claimed" value="toy_claimed" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Adopter Name">
                  <el-input v-model="diaryInput.adopter_name" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.adopter_name" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.adopter_name = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['主人', '新主人', '小主人']" 
                      :key="suggestion"
                      @click="diaryInput.adopter_name = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Adoption Date">
                  <el-input v-model="diaryInput.adoption_date" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.adoption_date" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.adoption_date = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['2025-01-01', '2025-02-14', '2025-12-25']" 
                      :key="suggestion"
                      @click="diaryInput.adoption_date = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
                <el-form-item label="Initial Emotion">
                  <el-input v-model="diaryInput.initial_emotion" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="diaryInput.initial_emotion" 
                        type="text" 
                        size="small" 
                        @click="diaryInput.initial_emotion = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['兴奋', '紧张', '好奇']" 
                      :key="suggestion"
                      @click="diaryInput.initial_emotion = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
              </div>

              <el-form-item label="Sub-Agent">
                <el-select v-model="diaryInput.sub_agent" disabled placeholder="Auto-selected based on event category">
                  <el-option label="Interactive Agent" value="interactive_agent" />
                  <el-option label="Dialogue Agent" value="dialogue_agent" />
                  <el-option label="Neglect Agent" value="neglect_agent" />
                  <el-option label="Trending Agent" value="trending_agent" />
                  <el-option label="Weather Agent" value="weather_agent" />
                  <el-option label="Holiday Agent" value="holiday_agent" />
                  <el-option label="Friends Agent" value="friends_agent" />
                  <el-option label="Adoption Agent" value="adoption_agent" />
                </el-select>
                <span class="form-help">Automatically selected based on event category</span>
              </el-form-item>
            </el-form>
          </div>

          <div v-else-if="selectedAgent === 'sensor'" class="agent-form">
            <h4>Sensor Event Agent Test</h4>
            <el-form :model="sensorInput" label-width="120px">
              <el-form-item label="Sensor Type">
                <el-select v-model="sensorInput.sensor_type" placeholder="Select sensor type">
                  <el-option label="Touch" value="touch" />
                  <el-option label="Accelerometer" value="accelerometer" />
                  <el-option label="Gesture" value="gesture" />
                  <el-option label="Sound" value="sound" />
                  <el-option label="Light" value="light" />
                  <el-option label="Temperature" value="temperature" />
                </el-select>
              </el-form-item>
              <el-form-item label="Sensor Data">
                <el-input 
                  v-model="sensorInput.sensor_data_json" 
                  type="textarea" 
                  :rows="4"
                  placeholder='{"value": 1, "duration": 2.5}'
                />
              </el-form-item>
            </el-form>
          </div>

          <div v-else-if="selectedAgent === 'bazi'" class="agent-form">
            <h4>BaZi/WuXing Agent Test</h4>
            <el-form :model="baziInput" label-width="120px">
              <el-form-item label="Birth Year">
                <el-input-number v-model="baziInput.birth_year" :min="1900" :max="2100" />
              </el-form-item>
              <el-form-item label="Birth Month">
                <el-input-number v-model="baziInput.birth_month" :min="1" :max="12" />
              </el-form-item>
              <el-form-item label="Birth Day">
                <el-input-number v-model="baziInput.birth_day" :min="1" :max="31" />
              </el-form-item>
              <el-form-item label="Birth Hour">
                <el-input-number v-model="baziInput.birth_hour" :min="0" :max="23" />
              </el-form-item>
                <el-form-item label="Birthplace">
                  <el-input v-model="baziInput.birthplace" placeholder="Click a suggestion below or type your own">
                    <template #suffix>
                      <el-button 
                        v-if="baziInput.birthplace" 
                        type="text" 
                        size="small" 
                        @click="baziInput.birthplace = ''"
                        style="color: #999;"
                      >
                        ×
                      </el-button>
                    </template>
                  </el-input>
                  <div class="suggestion-tags">
                    <el-tag 
                      v-for="suggestion in ['北京', '上海', '广州']" 
                      :key="suggestion"
                      @click="baziInput.birthplace = suggestion"
                      class="suggestion-tag"
                      effect="plain"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </el-form-item>
            </el-form>
          </div>

          <div v-else-if="selectedAgent === 'event'" class="agent-form">
            <h4>Event Agent Test</h4>
            <el-form :model="eventInput" label-width="120px">
              <el-form-item label="Test Type">
                <el-radio-group v-model="eventInput.test_type">
                  <el-radio label="extract">Extract</el-radio>
                  <el-radio label="update">Update</el-radio>
                  <el-radio label="pipeline">Pipeline</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="Dialogue">
                <el-input 
                  v-model="eventInput.dialogue" 
                  type="textarea" 
                  :rows="3"
                  placeholder="输入对话内容..."
                />
              </el-form-item>
              <el-form-item v-if="eventInput.test_type === 'update'" label="Related Events">
                <el-input 
                  v-model="eventInput.related_events_json" 
                  type="textarea" 
                  :rows="3"
                  placeholder='[{"topic": "考试", "title": "考试压力"}]'
                />
              </el-form-item>
            </el-form>
          </div>

          <!-- LLM Provider Selection -->
          <el-divider />
          <div class="llm-config">
            <h4>LLM Configuration</h4>
            <el-form label-width="120px">
              <el-form-item label="Provider">
                <el-select v-model="selectedProvider" placeholder="Select LLM provider">
                  <el-option 
                    v-for="provider in enabledProviders" 
                    :key="provider.provider_name" 
                    :label="`${provider.provider_name} (${provider.model_name})`" 
                    :value="provider.provider_name"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="Force LLM">
                <el-switch v-model="forceLLM" />
                <span class="form-help">Disable local fallback</span>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>

      <!-- Test Results -->
      <el-col :span="8">
        <el-card class="test-results">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>Test Results</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="runTest"
                :loading="testing"
                :disabled="!canRunTest"
              >
                <el-icon><VideoPlay /></el-icon>
                Run Test
              </el-button>
            </div>
          </template>

          <div v-if="testResult" class="result-content">
            <el-alert 
              :title="testResult.success ? 'Test Successful' : 'Test Failed'"
              :type="testResult.success ? 'success' : 'error'"
              :closable="false"
              show-icon
            />
            
            <div class="result-details">
              <h4>Response Data:</h4>
              <el-input 
                v-model="formattedResult" 
                type="textarea" 
                :rows="15"
                readonly
                class="result-json"
              />
            </div>

            <div class="result-meta">
              <p><strong>Provider:</strong> {{ testResult.provider || 'Default' }}</p>
              <p><strong>Timestamp:</strong> {{ testResult.timestamp }}</p>
              <p><strong>Response Time:</strong> {{ testResult.responseTime }}ms</p>
            </div>
          </div>

          <div v-else class="no-results">
            <el-empty description="No test results yet">
              <el-button type="primary" @click="runTest" :disabled="!canRunTest">
                Run Your First Test
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useAppStore } from '@/stores/appStore'
import apiService from '@/services/apiService'
import { ElMessage } from 'element-plus'
import { 
  Cpu, 
  List, 
  Edit, 
  Document, 
  VideoPlay 
} from '@element-plus/icons-vue'

const appStore = useAppStore()

// LLM Configuration
const llmConfig = ref(null)
const enabledProviders = computed(() => {
  if (!llmConfig.value?.providers) return []
  return Object.values(llmConfig.value.providers).filter(provider => provider.enabled)
})

// Reactive data
const selectedAgent = ref('diary')
const selectedProvider = ref('zhipu')
const forceLLM = ref(false)
const testing = ref(false)
const testResult = ref(null)
const usingCustomPrompt = ref(false)
const customPromptData = ref(null)

// Agent configurations
const availableAgents = ref([
  {
    type: 'diary',
    name: 'Diary Agent',
    description: 'Generate diary entries from events'
  },
  {
    type: 'sensor',
    name: 'Sensor Event Agent',
    description: 'Translate sensor data to cute descriptions'
  },
  {
    type: 'bazi',
    name: 'BaZi/WuXing Agent',
    description: 'Calculate Chinese astrology elements'
  },
  {
    type: 'event',
    name: 'Event Agent',
    description: 'Extract and update events from dialogue'
  }
])

// Input data
const diaryInput = ref({
  event_category: 'human_toy_interactive_function',
  event_name: 'liked_interaction_once',
  sub_agent: '',
  // Dynamic fields based on event category
  interaction_type: '抚摸',
  duration: '5分钟',
  user_response: 'positive',
  toy_emotion: '开心',
  dialogue_content: '',
  emotional_tone: 'positive',
  topic: '',
  neglect_duration: '1天',
  neglect_type: 'no_dialogue',
  trend_type: 'celebration',
  trend_topic: '',
  social_sentiment: '积极',
  weather_type: '晴天',
  temperature: '25°C',
  preference: 'favorite',
  holiday_name: '春节',
  holiday_phase: 'approaching',
  celebration_activity: '',
  friend_action: 'made_new_friend',
  friend_name: '',
  social_context: '',
  adoption_status: 'toy_claimed',
  adopter_name: '',
  adoption_date: '',
  initial_emotion: ''
})

// Event categories and their corresponding event names
const eventCategories = ref({
  'human_toy_interactive_function': [
    'liked_interaction_once',
    'liked_interaction_3_to_5_times',
    'liked_interaction_over_5_times',
    'disliked_interaction_once',
    'disliked_interaction_3_to_5_times',
    'neutral_interaction_over_5_times'
  ],
  'human_toy_talk': [
    'positive_emotional_dialogue',
    'negative_emotional_dialogue'
  ],
  'unkeep_interactive': [
    'neglect_1_day_no_dialogue',
    'neglect_1_day_no_interaction',
    'neglect_3_days_no_dialogue',
    'neglect_3_days_no_interaction',
    'neglect_7_days_no_dialogue',
    'neglect_7_days_no_interaction',
    'neglect_15_days_no_interaction',
    'neglect_30_days_no_dialogue',
    'neglect_30_days_no_interaction'
  ],
  'trending_events': [
    'celebration',
    'disaster'
  ],
  'weather_events': [
    'favorite_weather',
    'dislike_weather',
    'favorite_season',
    'dislike_season'
  ],
  'holiday_events': [
    'approaching_holiday',
    'during_holiday',
    'holiday_ends'
  ],
  'friends_function': [
    'made_new_friend',
    'friend_deleted',
    'liked_single',
    'liked_3_to_5',
    'liked_5_plus',
    'disliked_single',
    'disliked_3_to_5',
    'disliked_5_plus'
  ],
  'adopted_function': [
    'toy_claimed'
  ]
})

const sensorInput = ref({
  sensor_type: 'touch',
  sensor_data_json: '{"value": 1, "duration": 2.5}'
})

const baziInput = ref({
  birth_year: 1990,
  birth_month: 5,
  birth_day: 20,
  birth_hour: 14,
  birthplace: '北京'
})

const eventInput = ref({
  test_type: 'extract',
  dialogue: '今天考试压力很大，很担心成绩',
  related_events_json: '[]'
})

// Computed
const availableProviders = computed(() => appStore.availableProviders)
const availableEventNames = computed(() => {
  return eventCategories.value[diaryInput.value.event_category] || []
})

const canRunTest = computed(() => {
  if (!selectedAgent.value) return false
  if (!selectedProvider.value) return false
  
  switch (selectedAgent.value) {
    case 'diary':
      return diaryInput.value.event_category && diaryInput.value.event_name
    case 'sensor':
      return sensorInput.value.sensor_type && sensorInput.value.sensor_data_json
    case 'bazi':
      return baziInput.value.birth_year && baziInput.value.birth_month
    case 'event':
      return eventInput.value.dialogue
    default:
      return false
  }
})

const formattedResult = computed(() => {
  if (!testResult.value) return ''
  return JSON.stringify(testResult.value, null, 2)
})

// Methods
const loadLLMConfig = async () => {
  try {
    const response = await apiService.getLLMConfig()
    if (response.success) {
      llmConfig.value = response.data
      // Set default provider to the first enabled provider
      if (enabledProviders.value.length > 0) {
        selectedProvider.value = enabledProviders.value[0].provider_name
      }
    }
  } catch (error) {
    console.error('Failed to load LLM config:', error)
    ElMessage.error('Failed to load LLM configuration')
  }
}

const onAgentChange = () => {
  testResult.value = null
}

const onEventCategoryChange = () => {
  // Reset event name when category changes
  diaryInput.value.event_name = ''
  
  // Automatically set sub-agent based on event category
  const categoryToSubAgent = {
    'human_toy_interactive_function': 'interactive_agent',
    'human_toy_talk': 'dialogue_agent',
    'unkeep_interactive': 'neglect_agent',
    'trending_events': 'trending_agent',
    'weather_events': 'weather_agent',
    'holiday_events': 'holiday_agent',
    'friends_function': 'friends_agent',
    'adopted_function': 'adoption_agent'
  }
  
  diaryInput.value.sub_agent = categoryToSubAgent[diaryInput.value.event_category] || ''
  
  // Reset all dynamic fields
  Object.keys(diaryInput.value).forEach(key => {
    if (key !== 'event_category' && key !== 'sub_agent') {
      diaryInput.value[key] = ''
    }
  })
}

const runTest = async () => {
  if (!canRunTest.value) return
  
  testing.value = true
  const startTime = Date.now()
  
  try {
    let result
    
    switch (selectedAgent.value) {
      case 'diary':
        // Check if we have custom prompt data
        if (usingCustomPrompt.value && customPromptData.value) {
          result = await testDiaryAgentWithCustomPrompt()
        } else {
          result = await testDiaryAgent()
        }
        break
      case 'sensor':
        result = await testSensorAgent()
        break
      case 'bazi':
        result = await testBaziAgent()
        break
      case 'event':
        result = await testEventAgent()
        break
      default:
        throw new Error('Unknown agent type')
    }
    
    const responseTime = Date.now() - startTime
    testResult.value = {
      ...result,
      provider: selectedProvider.value,
      responseTime,
      timestamp: new Date().toISOString()
    }
    
    ElMessage.success('Test completed successfully!')
    
  } catch (error) {
    testResult.value = {
      success: false,
      error: error.message,
      provider: selectedProvider.value,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString()
    }
    ElMessage.error(`Test failed: ${error.message}`)
  } finally {
    testing.value = false
  }
}

const testDiaryAgent = async () => {
  const payload = {
    event_category: diaryInput.value.event_category,
    event_name: diaryInput.value.event_name
  }
  
  // Add sub_agent if specified
  if (diaryInput.value.sub_agent) {
    payload.sub_agent = diaryInput.value.sub_agent
  }
  
  // Add dynamic fields based on event category
  const category = diaryInput.value.event_category
  switch (category) {
    case 'human_toy_interactive_function':
      if (diaryInput.value.interaction_type) payload.interaction_type = diaryInput.value.interaction_type
      if (diaryInput.value.duration) payload.duration = diaryInput.value.duration
      if (diaryInput.value.user_response) payload.user_response = diaryInput.value.user_response
      if (diaryInput.value.toy_emotion) payload.toy_emotion = diaryInput.value.toy_emotion
      break
    case 'human_toy_talk':
      if (diaryInput.value.dialogue_content) payload.dialogue_content = diaryInput.value.dialogue_content
      if (diaryInput.value.emotional_tone) payload.emotional_tone = diaryInput.value.emotional_tone
      if (diaryInput.value.topic) payload.topic = diaryInput.value.topic
      break
    case 'unkeep_interactive':
      if (diaryInput.value.neglect_duration) payload.neglect_duration = diaryInput.value.neglect_duration
      if (diaryInput.value.neglect_type) payload.neglect_type = diaryInput.value.neglect_type
      if (diaryInput.value.toy_emotion) payload.toy_emotion = diaryInput.value.toy_emotion
      break
    case 'trending_events':
      if (diaryInput.value.trend_type) payload.trend_type = diaryInput.value.trend_type
      if (diaryInput.value.trend_topic) payload.trend_topic = diaryInput.value.trend_topic
      if (diaryInput.value.social_sentiment) payload.social_sentiment = diaryInput.value.social_sentiment
      break
    case 'weather_events':
      if (diaryInput.value.weather_type) payload.weather_type = diaryInput.value.weather_type
      if (diaryInput.value.temperature) payload.temperature = diaryInput.value.temperature
      if (diaryInput.value.preference) payload.preference = diaryInput.value.preference
      break
    case 'holiday_events':
      if (diaryInput.value.holiday_name) payload.holiday_name = diaryInput.value.holiday_name
      if (diaryInput.value.holiday_phase) payload.holiday_phase = diaryInput.value.holiday_phase
      if (diaryInput.value.celebration_activity) payload.celebration_activity = diaryInput.value.celebration_activity
      break
    case 'friends_function':
      if (diaryInput.value.friend_action) payload.friend_action = diaryInput.value.friend_action
      if (diaryInput.value.friend_name) payload.friend_name = diaryInput.value.friend_name
      if (diaryInput.value.social_context) payload.social_context = diaryInput.value.social_context
      break
    case 'adopted_function':
      if (diaryInput.value.adoption_status) payload.adoption_status = diaryInput.value.adoption_status
      if (diaryInput.value.adopter_name) payload.adopter_name = diaryInput.value.adopter_name
      if (diaryInput.value.adoption_date) payload.adoption_date = diaryInput.value.adoption_date
      if (diaryInput.value.initial_emotion) payload.initial_emotion = diaryInput.value.initial_emotion
      break
  }
  
  return await apiService.testDiaryAgent(payload)
}

const testDiaryAgentWithCustomPrompt = async () => {
  const payload = {
    event_category: diaryInput.value.event_category,
    event_name: diaryInput.value.event_name
  }
  
  // Add sub_agent if specified
  if (diaryInput.value.sub_agent) {
    payload.sub_agent = diaryInput.value.sub_agent
  }
  
  // Add dynamic fields based on event category
  const category = diaryInput.value.event_category
  switch (category) {
    case 'human_toy_interactive_function':
      if (diaryInput.value.interaction_type) payload.interaction_type = diaryInput.value.interaction_type
      if (diaryInput.value.duration) payload.duration = diaryInput.value.duration
      if (diaryInput.value.user_response) payload.user_response = diaryInput.value.user_response
      if (diaryInput.value.toy_emotion) payload.toy_emotion = diaryInput.value.toy_emotion
      break
    case 'human_toy_talk':
      if (diaryInput.value.dialogue_content) payload.dialogue_content = diaryInput.value.dialogue_content
      if (diaryInput.value.emotional_tone) payload.emotional_tone = diaryInput.value.emotional_tone
      if (diaryInput.value.topic) payload.topic = diaryInput.value.topic
      break
    case 'unkeep_interactive':
      if (diaryInput.value.neglect_duration) payload.neglect_duration = diaryInput.value.neglect_duration
      if (diaryInput.value.last_interaction) payload.last_interaction = diaryInput.value.last_interaction
      if (diaryInput.value.toy_emotion) payload.toy_emotion = diaryInput.value.toy_emotion
      break
    case 'trending_events':
      if (diaryInput.value.trend_topic) payload.trend_topic = diaryInput.value.trend_topic
      if (diaryInput.value.social_sentiment) payload.social_sentiment = diaryInput.value.social_sentiment
      if (diaryInput.value.trend_impact) payload.trend_impact = diaryInput.value.trend_impact
      break
    case 'weather_events':
      if (diaryInput.value.weather_type) payload.weather_type = diaryInput.value.weather_type
      if (diaryInput.value.temperature) payload.temperature = diaryInput.value.temperature
      if (diaryInput.value.weather_impact) payload.weather_impact = diaryInput.value.weather_impact
      break
    case 'holiday_events':
      if (diaryInput.value.holiday_name) payload.holiday_name = diaryInput.value.holiday_name
      if (diaryInput.value.celebration_activity) payload.celebration_activity = diaryInput.value.celebration_activity
      if (diaryInput.value.holiday_mood) payload.holiday_mood = diaryInput.value.holiday_mood
      break
    case 'friends_function':
      if (diaryInput.value.friend_action) payload.friend_action = diaryInput.value.friend_action
      if (diaryInput.value.friend_name) payload.friend_name = diaryInput.value.friend_name
      if (diaryInput.value.social_context) payload.social_context = diaryInput.value.social_context
      break
    case 'adopted_function':
      if (diaryInput.value.adoption_status) payload.adoption_status = diaryInput.value.adoption_status
      if (diaryInput.value.adopter_name) payload.adopter_name = diaryInput.value.adopter_name
      if (diaryInput.value.adoption_date) payload.adoption_date = diaryInput.value.adoption_date
      if (diaryInput.value.initial_emotion) payload.initial_emotion = diaryInput.value.initial_emotion
      break
  }
  
  // Use custom prompt data
  const customPrompt = {
    system_prompt: customPromptData.value.system_prompt,
    user_prompt_template: customPromptData.value.user_prompt_template,
    output_format: customPromptData.value.output_format,
    validation_rules: customPromptData.value.validation_rules
  }
  
  return await apiService.testDiaryAgentWithCustomPrompt(payload, customPrompt)
}

const testSensorAgent = async () => {
  const sensorData = JSON.parse(sensorInput.value.sensor_data_json)
  const payload = {
    sensor_type: sensorInput.value.sensor_type,
    ...sensorData,
    provider: selectedProvider.value,
    force_llm: forceLLM.value
  }
  return await apiService.testSensorAgent(payload)
}

const testBaziAgent = async () => {
  const payload = {
    birth_year: baziInput.value.birth_year,
    birth_month: baziInput.value.birth_month,
    birth_day: baziInput.value.birth_day,
    birth_hour: baziInput.value.birth_hour,
    birthplace: baziInput.value.birthplace
  }
  return await apiService.testBaziAgent(payload, selectedProvider.value)
}

const testEventAgent = async () => {
  const payload = {
    provider: selectedProvider.value,
    force_llm: forceLLM.value
  }
  
  switch (eventInput.value.test_type) {
    case 'extract':
      return await apiService.testEventExtract({
        chat_uuid: 'test-cu-1',
        chat_event_uuid: 'test-evt-1',
        memory_uuid: 'test-mem-1',
        dialogue: eventInput.value.dialogue,
        ...payload
      })
    case 'update':
      const relatedEvents = JSON.parse(eventInput.value.related_events_json)
      return await apiService.testEventUpdate(
        { topic: 'test', title: 'test', summary: 'test' },
        relatedEvents,
        selectedProvider.value
      )
    case 'pipeline':
      return await apiService.testEventPipeline(
        {
          chat_uuid: 'test-cu-1',
          chat_event_uuid: 'test-evt-1',
          memory_uuid: 'test-mem-1',
          dialogue: eventInput.value.dialogue
        },
        [],
        selectedProvider.value
      )
  }
}

// Lifecycle
onMounted(async () => {
  await loadLLMConfig()
  
  // Check if we have test prompt data from Prompt Editor
  const testPromptData = sessionStorage.getItem('testPromptData')
  if (testPromptData) {
    try {
      const promptData = JSON.parse(testPromptData)
      
      // Set the agent type based on the prompt data
      if (promptData.agent_type) {
        selectedAgent.value = promptData.agent_type
      }
      
      // Store custom prompt data for display
      customPromptData.value = promptData
      usingCustomPrompt.value = true
      
      // Show a notification that we're using a custom prompt
      ElMessage.info(`Using custom prompt from Prompt Editor (${promptData.agent_type})`)
      
      // Clear the stored data after using it
      sessionStorage.removeItem('testPromptData')
    } catch (error) {
      console.error('Failed to parse test prompt data:', error)
    }
  }
  
  // Initialize sub-agent based on default event category
  onEventCategoryChange()
})
</script>

<style scoped>
.suggestion-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #dcdfe6;
  background-color: #f5f7fa;
  color: #606266;
}

.suggestion-tag:hover {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h2 {
  margin: 0 0 10px 0;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.agent-selector {
  height: fit-content;
}

.agent-radio {
  width: 100%;
  margin-bottom: 15px;
}

.agent-info {
  margin-left: 10px;
}

.agent-name {
  font-weight: 600;
  color: #333;
}

.agent-desc {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.input-config {
  height: fit-content;
}

.agent-form h4 {
  margin: 0 0 20px 0;
  color: #333;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.llm-config h4 {
  margin: 20px 0 15px 0;
  color: #333;
}

.form-help {
  margin-left: 10px;
  font-size: 12px;
  color: #666;
}

.test-results {
  height: fit-content;
}

.result-content {
  margin-top: 20px;
}

.result-details {
  margin: 20px 0;
}

.result-details h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.result-json {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.result-meta {
  margin-top: 15px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 4px;
}

.result-meta p {
  margin: 5px 0;
  font-size: 14px;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
}

.custom-prompt-info {
  margin-top: 10px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.custom-prompt-info p {
  margin: 5px 0;
  font-size: 14px;
  color: #333;
}

.custom-prompt-info strong {
  color: #409eff;
}
</style>
