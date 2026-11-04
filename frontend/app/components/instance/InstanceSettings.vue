<script setup lang="ts">
import HologramLight from '~/components/ui/HologramLight.vue'
import ExpandTransition from '~/components/ui/ExpandTransition.vue'
import ServerIdentity from './ServerIdentity.vue'
import AddonManager from './AddonManager.vue'
import { propertyFields } from '../../../i18n/instance'
import { instancePropertyKeys, parseServerProperties } from '~/utils/serverProperties'

const props = defineProps<{ instanceId: string; status?: string }>()
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const tr = usePanelText()
const { instanceRequest, getErrorMessage } = useInstanceApi(() => props.instanceId)
// 导航与内容共用明确状态，并按分类重建表单。
const activeSection = ref<'instance' | 'properties' | 'mods' | 'plugins'>('instance')
const loading = ref(true)
const loaded = ref(false)
const saving = ref(false)
const search = ref('')
const notice = ref('')
const failed = ref(false)
const apiCompatible = ref(true)
const settings = reactive({
  runtime_mode: 'java',
  secondary_port: null as number | null,
  name: '',
  instance_path: '',
  port: 25565,
  memory_mb: 4096,
  java_version: '21',
  java_path: '',
  jar_name: 'server.jar',
  jvm_args: '',
  rcon_enabled: true,
  rcon_port: 25575,
  rcon_password: '',
  auto_restart: false,
  ignore_eula: false,
  property_values: {} as Record<string, string>,
  server_ip: '',
  query_enabled: false,
  query_port: 25565,
})
const running = computed(() => props.status === 'running' || props.status === 'deploying')
const inputClass =
  'w-full border border-border bg-background px-3 py-2.5 text-sm text-text-primary outline-none focus:border-brand disabled:opacity-50'
const toggleDefinitions = [
  { key: 'rcon_enabled', label: 'settingsRcon' },
  { key: 'auto_restart', label: 'settingsRestart' },
  { key: 'ignore_eula', label: 'settingsEula' },
  { key: 'query_enabled', label: 'property_enable_query' },
] as const
const toggles = computed(() =>
  toggleDefinitions.filter(
    (item) => settings.runtime_mode !== 'bedrock' || !['rcon_enabled', 'query_enabled'].includes(item.key),
  ),
)
// 按当前核心已有属性生成控件，保留额外属性。
const groups = ['General', 'Game', 'World', 'Performance', 'Network', 'Resource', 'Advanced']
const fields = computed(() =>
  Object.entries(settings.property_values)
    .filter(([key]) => !instancePropertyKeys.has(key))
    .map(([key, value]) => {
      const known = propertyFields.find((item) => item.key === key)
      return {
        key,
        label: known?.label,
        group: known?.group || 'settingsGroupAdvanced',
        type: known?.type || (/^(true|false)$/.test(value) ? 'boolean' : /^-?\d+$/.test(value) ? 'number' : 'text'),
        min: known?.min,
        max: known?.max,
      }
    })
    .filter((item) =>
      `${item.key} ${item.label ? t(item.label) : ''}`.toLowerCase().includes(search.value.toLowerCase()),
    ),
)
const fieldGroups = computed(() =>
  groups
    .map((group) => ({
      key: 'settingsGroup' + group,
      fields: fields.value.filter((field) => field.group === 'settingsGroup' + group),
    }))
    .filter((group) => group.fields.length),
)

// 实例连接参数统一写回底层属性文件。
function syncProperties() {
  Object.assign(settings.property_values, {
    'server-port': String(settings.port),
    'enable-rcon': String(settings.rcon_enabled),
    'rcon.port': String(settings.rcon_port),
    'rcon.password': settings.rcon_password,
    'server-ip': settings.server_ip,
  })
  if ('enable-query' in settings.property_values)
    settings.property_values['enable-query'] = String(settings.query_enabled)
  if ('query.port' in settings.property_values) settings.property_values['query.port'] = String(settings.query_port)
}
watch(
  () => [
    settings.port,
    settings.rcon_enabled,
    settings.rcon_port,
    settings.rcon_password,
    settings.server_ip,
    settings.query_enabled,
    settings.query_port,
  ],
  () => {
    if (loaded.value) syncProperties()
  },
)
function setProperty(key: string, value: string) {
  settings.property_values[key] = value
}
function options(type: string) {
  return type === 'gamemode'
    ? [
        ['survival', 'optionSurvival'],
        ['creative', 'optionCreative'],
        ['adventure', 'optionAdventure'],
        ['spectator', 'optionSpectator'],
      ]
    : [
        ['peaceful', 'optionPeaceful'],
        ['easy', 'optionEasy'],
        ['normal', 'optionNormal'],
        ['hard', 'optionHard'],
      ]
}
async function load() {
  // 读取持久化设置及当前核心属性。
  loading.value = true
  try {
    const result = await instanceRequest<{ settings: Partial<typeof settings> & { server_properties?: string } }>(
      '/settings',
    )
    // 旧后端仍可展示全部属性，但必须升级后才能保存。
    apiCompatible.value = result.settings.property_values != null
    Object.assign(settings, result.settings)
    settings.property_values =
      result.settings.property_values ?? parseServerProperties(result.settings.server_properties || '')
    const values = settings.property_values
    settings.rcon_enabled = values['enable-rcon'] === 'true'
    settings.rcon_port = Number(values['rcon.port'] || result.settings.rcon_port || 25575)
    settings.rcon_password = values['rcon.password'] ?? result.settings.rcon_password ?? ''
    settings.server_ip = values['server-ip'] || ''
    settings.query_enabled = values['enable-query'] === 'true'
    settings.query_port = Number(values['query.port'] || 25565)
    loaded.value = true
  } catch (error) {
    failed.value = true
    notice.value = getErrorMessage(error, t('settingsLoadError'))
  } finally {
    loading.value = false
  }
}
async function save() {
  // 停服后保存，避免游戏进程覆盖文件。
  if (!loaded.value || saving.value || running.value || !apiCompatible.value) return
  saving.value = true
  notice.value = ''
  syncProperties()
  try {
    await instanceRequest('/settings', { method: 'PUT', body: settings })
    failed.value = false
    notice.value = t('settingsSaved')
    emit('saved')
  } catch (error) {
    failed.value = true
    notice.value = getErrorMessage(error, t('settingsSaveError'))
  } finally {
    saving.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="grid items-start gap-6 lg:grid-cols-[220px_minmax(0,1fr)]">
    <AtmosphereCard>
      <nav class="space-y-2" :aria-label="t('settingsInstance')">
        <p class="mb-5 font-mono text-[10px] tracking-[0.2em] text-text-secondary">/ CONFIGURATION</p>
        <button
          v-for="item in ['instance', 'properties', 'mods', 'plugins']"
          :key="item"
          type="button"
          class="settings-tab flex w-full items-center justify-between border-l-2 px-4 py-3 text-left text-sm"
          :class="
            activeSection === item
              ? 'border-brand text-brand'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          "
          @click="activeSection = item as typeof activeSection"
        >
          {{
            item === 'mods'
              ? tr('模组列表', 'MOD LIST', 'MOD 一覧')
              : item === 'plugins'
                ? tr('插件列表', 'PLUGIN LIST', 'プラグイン一覧')
                : t(item === 'instance' ? 'settingsInstance' : 'settingsProperties')
          }}
          <span class="transition-transform duration-300" :class="activeSection === item ? 'translate-x-1' : ''"
            >→</span
          >
        </button>
      </nav>
    </AtmosphereCard>
    <div class="min-w-0">
      <ExpandTransition replace>
        <AtmosphereCard v-if="activeSection === 'instance' || activeSection === 'properties'" key="configuration">
          <form class="space-y-7" @submit.prevent="save">
            <header class="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-6">
              <div>
                <p class="font-mono text-[10px] tracking-[0.2em] text-brand">
                  / {{ activeSection === 'instance' ? 'INSTANCE SETTINGS' : 'SERVER.PROPERTIES' }}
                </p>
                <h2 class="mt-3 font-serif text-2xl text-text-primary">
                  {{ t(activeSection === 'instance' ? 'settingsInstance' : 'settingsProperties') }}
                </h2>
              </div>
              <button
                type="submit"
                :disabled="!loaded || saving || running || !apiCompatible"
                class="border border-border px-5 py-3 font-mono text-xs text-brand transition hover:border-brand disabled:cursor-not-allowed disabled:opacity-40"
              >
                {{ t(saving ? 'settingsSaving' : 'settingsSave') }}
              </button>
            </header>
            <p v-if="loading" class="text-sm text-text-secondary" role="status">{{ t('settingsLoading') }}</p>
            <p
              v-if="!apiCompatible"
              role="alert"
              class="border-l-2 border-amber-400 pl-4 text-sm leading-6 text-amber-300"
            >
              {{ t('settingsBackendOutdated') }}
            </p>
            <p v-if="running" class="border-l-2 border-brand pl-4 text-sm leading-6 text-text-secondary">
              {{ t('settingsStopFirst') }}
            </p>
            <p v-if="notice" role="status" :class="failed ? 'text-red-400' : 'text-brand'" class="text-sm">
              {{ notice }}
            </p>
            <fieldset v-if="loaded" :disabled="saving" class="min-w-0 space-y-7">
              <ExpandTransition replace>
                <div
                  v-if="activeSection === 'instance'"
                  key="instance"
                  class="space-y-7"
                  data-settings-panel="instance"
                >
                  <div class="grid gap-5 md:grid-cols-2">
                    <label class="space-y-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsName') }}</span
                      ><input v-model="settings.name" required maxlength="120" :class="inputClass"
                    /></label>
                    <label class="space-y-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsPort') }}</span
                      ><input
                        v-model.number="settings.port"
                        type="number"
                        min="1"
                        max="65535"
                        required
                        :class="inputClass"
                    /></label>
                    <label class="space-y-2 md:col-span-2"
                      ><span class="text-xs text-text-secondary">{{ t('property_server_ip') }}</span
                      ><input v-model="settings.server_ip" :class="inputClass" spellcheck="false"
                    /></label>
                    <label class="space-y-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsMemory') }}</span
                      ><input
                        v-model.number="settings.memory_mb"
                        type="number"
                        min="512"
                        max="131072"
                        step="128"
                        required
                        :class="inputClass"
                    /></label>
                    <label v-if="settings.runtime_mode !== 'bedrock'" class="space-y-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsJava') }}</span
                      ><AtmosphereSelect
                        v-model="settings.java_version"
                        :label="t('settingsJava')"
                        :options="['8', '17', '21', '25'].map((value) => ({ value, label: 'Java ' + value }))"
                    /></label>
                    <label v-if="settings.runtime_mode !== 'bedrock'" class="space-y-2 md:col-span-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsJavaPath') }}</span
                      ><input v-model="settings.java_path" :class="inputClass" spellcheck="false" /><small
                        class="block leading-5 text-text-secondary"
                        >{{ t('settingsJavaHint') }}</small
                      ></label
                    >
                    <label class="space-y-2 md:col-span-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsTarget') }}</span
                      ><input v-model="settings.jar_name" :class="inputClass" required spellcheck="false"
                    /></label>
                    <label class="space-y-2 md:col-span-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsPath') }}</span
                      ><input :value="settings.instance_path" readonly :class="inputClass"
                    /></label>
                    <label v-if="settings.runtime_mode !== 'bedrock'" class="space-y-2 md:col-span-2"
                      ><span class="text-xs text-text-secondary">{{ t('settingsJvm') }}</span
                      ><input v-model="settings.jvm_args" :class="inputClass" spellcheck="false" /><small
                        class="block leading-5 text-text-secondary"
                        >{{ t('settingsJvmHint') }}</small
                      ></label
                    >
                  </div>
                  <label v-if="settings.runtime_mode === 'bedrock'" class="block space-y-2"
                    ><span class="text-xs text-text-secondary">IPv6 UDP PORT</span
                    ><input
                      v-model.number="settings.secondary_port"
                      type="number"
                      min="1"
                      max="65535"
                      required
                      :class="inputClass"
                  /></label>
                  <div class="grid gap-3 border-t border-border pt-6 sm:grid-cols-2">
                    <div
                      v-for="item in toggles"
                      :key="item.key"
                      class="flex items-center justify-between gap-4 border border-border px-4 py-4 text-sm text-text-primary"
                    >
                      <span>{{ t(item.label) }}</span>
                      <button
                        type="button"
                        role="switch"
                        :aria-label="t(item.label)"
                        :aria-checked="settings[item.key]"
                        class="instance-switch"
                        :class="{ 'is-on': settings[item.key] }"
                        @click="settings[item.key] = !settings[item.key]"
                      >
                        <span class="switch-thumb" />
                      </button>
                    </div>
                    <p class="text-xs leading-6 text-text-secondary sm:col-span-2">
                      {{ t('settingsRestartHint') }}
                      <a
                        href="https://aka.ms/MinecraftEULA"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="text-brand underline"
                        >Minecraft EULA</a
                      >
                    </p>
                  </div>
                  <ExpandTransition>
                    <div v-if="settings.rcon_enabled" class="grid gap-5 pt-2 md:grid-cols-2" data-rcon-fields>
                      <label class="space-y-2"
                        ><span class="text-xs text-text-secondary">{{ t('settingsRconPort') }}</span
                        ><input
                          v-model.number="settings.rcon_port"
                          type="number"
                          min="1"
                          max="65535"
                          required
                          :class="inputClass"
                      /></label>
                      <label class="space-y-2"
                        ><span class="text-xs text-text-secondary">{{ t('settingsRconPassword') }}</span
                        ><input
                          v-model="settings.rcon_password"
                          type="password"
                          autocomplete="new-password"
                          required
                          :class="inputClass"
                      /></label>
                    </div>
                  </ExpandTransition>
                  <ExpandTransition>
                    <label v-if="settings.query_enabled" class="block space-y-2"
                      ><span class="text-xs text-text-secondary">{{ t('property_query_port') }}</span
                      ><input
                        v-model.number="settings.query_port"
                        type="number"
                        min="1"
                        max="65535"
                        required
                        :class="inputClass"
                    /></label>
                  </ExpandTransition>
                </div>
                <div v-else key="properties" class="space-y-7" data-settings-panel="properties">
                  <p class="text-xs leading-6 text-text-secondary">{{ t('settingsPresent') }}</p>
                  <input
                    v-model="search"
                    type="search"
                    :placeholder="t('settingsSearch')"
                    :aria-label="t('settingsSearch')"
                    :class="inputClass"
                  />
                  <p v-if="!fieldGroups.length" class="py-8 text-center text-sm text-text-secondary">
                    {{ t('settingsEmpty') }}
                  </p>
                  <section v-for="group in fieldGroups" :key="group.key" class="space-y-5 border-t border-border pt-6">
                    <h3 class="font-serif text-lg text-brand">{{ t(group.key) }}</h3>
                    <p v-if="group.key === 'settingsGroupWorld'" class="text-xs leading-6 text-text-secondary">
                      {{ t('settingsWorldHint') }}
                    </p>
                    <div class="grid gap-x-6 gap-y-5 md:grid-cols-2">
                      <div v-for="field in group.fields" :key="field.key" class="min-w-0 space-y-2">
                        <span class="block text-sm text-text-primary">{{
                          field.label ? t(field.label) : field.key
                        }}</span>
                        <span class="block font-mono text-[10px] text-text-secondary">{{ field.key }}</span>
                        <button
                          v-if="field.type === 'boolean'"
                          type="button"
                          role="switch"
                          :aria-label="field.label ? t(field.label) : field.key"
                          :aria-checked="settings.property_values[field.key] === 'true'"
                          class="flex w-full items-center justify-between border px-3 py-2.5 text-sm transition"
                          :class="
                            settings.property_values[field.key] === 'true'
                              ? 'border-brand text-brand'
                              : 'border-border text-text-secondary'
                          "
                          @click="
                            setProperty(field.key, settings.property_values[field.key] === 'true' ? 'false' : 'true')
                          "
                        >
                          {{ t(settings.property_values[field.key] === 'true' ? 'settingsOn' : 'settingsOff') }}
                          <HologramLight :active="settings.property_values[field.key] === 'true'" />
                        </button>
                        <AtmosphereSelect
                          v-else-if="field.type === 'gamemode' || field.type === 'difficulty'"
                          :model-value="settings.property_values[field.key] || ''"
                          :label="field.label ? t(field.label) : field.key"
                          :options="options(field.type).map(([value, label]) => ({ value: value!, label: t(label!) }))"
                          @update:model-value="setProperty(field.key, $event)"
                        />
                        <input
                          v-else
                          :value="settings.property_values[field.key]"
                          :type="field.type"
                          :min="field.min"
                          :max="field.max"
                          :required="field.type === 'number'"
                          :class="inputClass"
                          spellcheck="false"
                          @input="setProperty(field.key, ($event.target as HTMLInputElement).value)"
                        />
                      </div>
                    </div>
                  </section>
                </div>
              </ExpandTransition>
            </fieldset>
            <ServerIdentity
              v-if="activeSection === 'instance' && loaded"
              :instance-id="instanceId"
              :running="running"
            />
          </form>
        </AtmosphereCard>
        <AddonManager v-else :key="activeSection" :kind="activeSection" :instance-id="instanceId" />
      </ExpandTransition>
    </div>
  </div>
</template>

<style scoped>
/* 玻璃轨道与发光滑块共用缓动。 */
.settings-tab {
  transition:
    color 240ms ease,
    border-color 240ms ease,
    background 240ms ease;
}
.settings-tab:hover {
  background: color-mix(in srgb, var(--brand) 5%, transparent);
}
.instance-switch {
  position: relative;
  width: 48px;
  height: 26px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 0;
  background: var(--background);
  box-shadow: inset 0 1px 5px #0004;
  transition:
    border-color 260ms ease,
    background 260ms ease,
    box-shadow 260ms ease;
}
.switch-thumb::after {
  content: '';
  position: absolute;
  top: 3px;
  bottom: 3px;
  left: 8px;
  width: 1px;
  background: color-mix(in srgb, var(--background) 75%, transparent);
  box-shadow: 1px 0 0 #ffffff33;
}
.switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 0;
  background: var(--brand);
  opacity: 0.55;
  transition:
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 260ms ease,
    box-shadow 260ms ease;
}
.instance-switch.is-on {
  border-color: #67e8ad99;
  background: #40ed9a14;
  box-shadow:
    inset 0 1px 5px #0003,
    0 0 12px #40ed9a12;
}
.instance-switch.is-on .switch-thumb {
  transform: translateX(22px);
  opacity: 1;
  background: #c9ffe2;
  box-shadow: 0 0 7px #53ffa683;
}
/* 按住时方块反色代替按钮下沉。 */
.instance-switch:active {
  transform: none;
}
.instance-switch:active .switch-thumb {
  background: #c9ffe2;
  opacity: 1;
  transition:
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.12s ease,
    background 0.12s ease,
    box-shadow 0.12s ease;
}
.instance-switch.is-on:active .switch-thumb {
  background: var(--text-secondary);
  opacity: 0.55;
  box-shadow: none;
}
.instance-switch:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 3px;
}
@media (prefers-reduced-motion: reduce) {
  .instance-switch,
  .switch-thumb {
    transition: none;
  }
}
</style>
