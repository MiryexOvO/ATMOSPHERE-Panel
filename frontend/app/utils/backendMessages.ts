// 后端错误信息目前只有中文；这里把中文原文映射到 i18n 键，翻译在 i18n/common.ts。
export const backendMessageKeys: Record<string, string> = {
  'IPv6 UDP 端口已被其他实例或任务预留': 'msg_backend_ipv6_udp_port_is_reserved_by_another_instanc',
  'IPv6 UDP 端口重复或已占用': 'msg_backend_ipv6_udp_port_is_duplicated_or_in_use',
  不能覆盖目录: 'msg_backend_cannot_overwrite_a_directory',
  不能禁用或降低自己的管理员权限: 'msg_backend_you_cannot_disable_or_downgrade_your_own_adm',
  部署任务不存在: 'msg_backend_deployment_task_not_found',
  服务端端口已被占用: 'msg_backend_server_port_is_already_in_use',
  服务端属性键或值无效: 'msg_backend_invalid_server_property_key_or_value',
  该实例或端口正在部署: 'msg_backend_this_instance_or_port_is_being_deployed',
  '该实例正在部署，请等待完成': 'msg_backend_this_instance_is_deploying_wait_for_it_to_fi',
  '仅支持 ZIP、TAR.GZ 或 TGZ': 'msg_backend_only_zip_tar_gz_or_tgz_is_supported',
  每次只能发送一条指令: 'msg_backend_only_one_command_can_be_sent_at_a_time',
  '密码需要 8–72 字节': 'msg_backend_password_must_be_8_72_bytes',
  启动目标不存在或路径无效: 'msg_backend_launch_target_does_not_exist_or_the_path_is_',
  '请设置 RCON 密码，并使用不同于游戏端口的 RCON 端口': 'msg_backend_set_an_rcon_password_and_use_an_rcon_port_di',
  '请先停止实例再保存设置，避免服务端覆盖配置文件': 'msg_backend_stop_the_instance_before_saving_to_avoid_the',
  请选择游戏版本: 'msg_backend_select_a_game_version',
  '实例 ID 或端口已存在或正在部署': 'msg_backend_instance_id_or_port_already_exists_or_is_bei',
  '实例 ID 或端口已存在，请管理已有实例或更换端口': 'msg_backend_instance_id_or_port_already_exists_manage_th',
  '实例 ID 无效': 'msg_backend_invalid_instance_id',
  '实例 ID、端口或运行环境无效': 'msg_backend_invalid_instance_id_port_or_runtime',
  实例不存在: 'msg_backend_instance_not_found',
  实例进程已退出: 'msg_backend_instance_process_has_exited',
  实例目录不存在: 'msg_backend_instance_directory_not_found',
  实例未运行或RCON未配置: 'msg_backend_instance_is_not_running_or_rcon_is_not_confi',
  '实例未运行或 RCON 未配置': 'msg_backend_instance_is_not_running_or_rcon_is_not_confi_2',
  '实例正在部署，请等待完成': 'msg_backend_instance_is_deploying_wait_for_it_to_finish',
  世界生成参数必须是有效JSON: 'msg_backend_world_generation_parameters_must_be_valid_js',
  未登录: 'msg_backend_not_signed_in',
  '文件不存在或超过 5MB': 'msg_backend_file_not_found_or_larger_than_5mb',
  '文件超过 5MB': 'msg_backend_file_exceeds_5mb',
  用户名已存在: 'msg_backend_username_already_exists',
  账户不存在: 'msg_backend_account_not_found',
  'PNG 不完整': 'msg_backend_incomplete_png',
  'PNG 校验失败': 'msg_backend_png_validation_failed',
  不可删除他人的任务: 'msg_backend_you_can_t_delete_others_tasks',
  不可修改他人的任务: 'msg_backend_you_can_t_modify_others_tasks',
  不可运行他人的任务: 'msg_backend_you_can_t_run_others_tasks',
  不能删除当前账户: 'msg_backend_you_can_t_delete_the_current_account',
  当前密码不正确: 'msg_backend_current_password_is_incorrect',
  导出失败: 'msg_backend_export_failed',
  登录尝试过多: 'msg_backend_too_many_login_attempts',
  二步验证已启用: 'msg_backend_two_factor_authentication_is_already_enabled',
  发布源尚无可访问的正式版本: 'msg_backend_no_accessible_stable_release_yet',
  更新包不存在: 'msg_backend_update_package_not_found',
  '官方 BDS 仅提供 Windows / Ubuntu x86_64 版本': 'msg_backend_official_bds_is_only_available_for_windows_u',
  获取官方基岩版版本失败: 'msg_backend_failed_to_fetch_official_bedrock_versions',
  检查更新失败: 'msg_backend_failed_to_check_for_updates',
  没有任务操作权限: 'msg_backend_no_permission_for_task_operations',
  没有所选实例的操作权限: 'msg_backend_no_permission_for_the_selected_instances',
  密码错误: 'msg_backend_incorrect_password',
  目标文件已存在: 'msg_backend_target_file_already_exists',
  请使用新版向导选择基岩版版本并确认EULA: 'msg_backend_use_the_new_wizard_to_pick_a_bedrock_version',
  请输入单行命令: 'msg_backend_enter_a_single_line_command',
  请输入验证器中的六位验证码: 'msg_backend_enter_the_six_digit_code_from_your_authentic',
  '请同意 Minecraft EULA，并设置不同的 IPv4 / IPv6 UDP 端口':
    'msg_backend_accept_the_minecraft_eula_and_set_different_',
  请先关闭HTTPS再替换证书: 'msg_backend_disable_https_before_replacing_the_certifica',
  请先停止实例: 'msg_backend_stop_the_instance_first',
  '请先停止实例，确保世界存档一致': 'msg_backend_stop_the_instance_first_to_keep_the_world_sa',
  任务不存在: 'msg_backend_task_not_found',
  尚未设置图标: 'msg_backend_no_icon_set_yet',
}

const CJK = /[\u4e00-\u9fff]/

const normalize = (value: string) => value.replace(/\s+/g, '')

// 返回对应的 i18n 键；未收录返回 null，由调用方决定回退。
export function translateBackendKey(message: string): string | null {
  if (!message || !CJK.test(message)) return null
  if (backendMessageKeys[message]) return backendMessageKeys[message]
  const target = normalize(message)
  for (const [zh, key] of Object.entries(backendMessageKeys)) {
    if (target.startsWith(normalize(zh))) return key
  }
  return null
}

export function hasCJK(value: string): boolean {
  return CJK.test(value)
}
