#!/usr/bin/env ruby

require "yaml"

ROOT = File.expand_path("..", __dir__)
SKILLS_DIR = File.join(ROOT, "skills")
EXPECTED_SKILLS = %w[
  complexity
  gr
  meaningful-contribution
  office-hours
  plan-ceo-review
  unsummarizable
].freeze

errors = []
skill_dirs = Dir.children(SKILLS_DIR).select do |entry|
  File.directory?(File.join(SKILLS_DIR, entry))
end.sort

errors << "expected #{EXPECTED_SKILLS.inspect}, found #{skill_dirs.inspect}" unless skill_dirs == EXPECTED_SKILLS

skill_dirs.each do |directory_name|
  skill_dir = File.join(SKILLS_DIR, directory_name)
  skill_path = File.join(skill_dir, "SKILL.md")

  unless File.file?(skill_path)
    errors << "#{directory_name}: missing SKILL.md"
    next
  end

  contents = File.read(skill_path)
  match = contents.match(/\A---\s*\n(.*?)\n---\s*\n/m)
  unless match
    errors << "#{directory_name}: missing YAML frontmatter"
    next
  end

  begin
    metadata = YAML.safe_load(match[1], permitted_classes: [], aliases: false)
  rescue Psych::SyntaxError => error
    errors << "#{directory_name}: invalid YAML (#{error.message.lines.first.strip})"
    next
  end

  errors << "#{directory_name}: frontmatter must be a mapping" unless metadata.is_a?(Hash)
  next unless metadata.is_a?(Hash)

  errors << "#{directory_name}: name must match its directory" unless metadata["name"] == directory_name
  description = metadata["description"]
  errors << "#{directory_name}: description must be non-empty" unless description.is_a?(String) && !description.strip.empty?
  errors << "#{directory_name}: contains an unresolved template marker" if contents.include?("[TODO")

  agent_path = File.join(skill_dir, "agents", "openai.yaml")
  next unless File.file?(agent_path)

  begin
    agent_metadata = YAML.safe_load(File.read(agent_path), permitted_classes: [], aliases: false)
    default_prompt = agent_metadata.dig("interface", "default_prompt")
    errors << "#{directory_name}: default prompt must mention $#{directory_name}" unless default_prompt&.include?("$#{directory_name}")
  rescue Psych::SyntaxError => error
    errors << "#{directory_name}: invalid agents/openai.yaml (#{error.message.lines.first.strip})"
  end
end

if errors.empty?
  puts "Validated #{skill_dirs.length} skills: #{skill_dirs.join(', ')}"
  exit 0
end

warn errors.map { |error| "- #{error}" }.join("\n")
exit 1
