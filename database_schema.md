-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.article_tags (
  id integer NOT NULL DEFAULT nextval('article_tags_id_seq'::regclass),
  article_id integer,
  tag_id integer,
  confidence numeric DEFAULT 1.00,
  source character varying DEFAULT 'ai'::character varying,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT article_tags_pkey PRIMARY KEY (id),
  CONSTRAINT article_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id),
  CONSTRAINT article_tags_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.news_articles(id)
);
CREATE TABLE public.keyword_mappings (
  id integer NOT NULL DEFAULT nextval('keyword_mappings_id_seq'::regclass),
  tag_id integer,
  keyword character varying NOT NULL,
  language character varying DEFAULT 'auto'::character varying,
  mapping_type character varying DEFAULT 'manual'::character varying,
  confidence numeric DEFAULT 1.00,
  match_method character varying DEFAULT 'exact'::character varying,
  is_active boolean DEFAULT true,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT keyword_mappings_pkey PRIMARY KEY (id),
  CONSTRAINT keyword_mappings_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id)
);
CREATE TABLE public.news_articles (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  original_url text NOT NULL UNIQUE,
  source text NOT NULL,
  title text NOT NULL,
  summary text NOT NULL,
  published_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  tags ARRAY DEFAULT '{}'::text[],
  topics jsonb DEFAULT '[]'::jsonb,
  CONSTRAINT news_articles_pkey PRIMARY KEY (id)
);
CREATE TABLE public.profiles (
  id uuid NOT NULL,
  platform_user_id text NOT NULL UNIQUE,
  username text,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT profiles_pkey PRIMARY KEY (id),
  CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
CREATE TABLE public.push_history (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id uuid NOT NULL,
  article_id bigint NOT NULL,
  pushed_at timestamp with time zone DEFAULT now(),
  batch_id text,
  CONSTRAINT push_history_pkey PRIMARY KEY (id),
  CONSTRAINT push_history_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.news_articles(id),
  CONSTRAINT push_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id)
);
CREATE TABLE public.subscriptions (
  user_id uuid NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  news_sources jsonb DEFAULT '[]'::jsonb,
  delivery_platform USER-DEFINED NOT NULL DEFAULT 'discord'::delivery_platforms,
  delivery_target text NOT NULL,
  push_frequency_hours integer NOT NULL DEFAULT 24,
  keywords jsonb DEFAULT '[]'::jsonb,
  summary_language USER-DEFINED NOT NULL DEFAULT 'zh-tw'::summary_languages,
  last_pushed_at timestamp with time zone,
  updated_at timestamp with time zone DEFAULT now(),
  push_frequency_type text DEFAULT 'daily'::text CHECK (push_frequency_type = ANY (ARRAY['daily'::text, 'twice'::text, 'thrice'::text])),
  last_push_window text,
  subscribed_tags ARRAY DEFAULT '{}'::text[],
  original_keywords ARRAY DEFAULT '{}'::text[],
  keywords_updated_at timestamp with time zone DEFAULT now(),
  tags_updated_at timestamp with time zone DEFAULT now(),
  guidance_completed boolean DEFAULT false,
  focus_score numeric DEFAULT 0.0,
  last_guidance_at timestamp with time zone,
  clustering_method text DEFAULT 'rule_based'::text,
  primary_topics ARRAY DEFAULT '{}'::text[],
  CONSTRAINT subscriptions_pkey PRIMARY KEY (user_id),
  CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id)
);
CREATE TABLE public.tags (
  id integer NOT NULL DEFAULT nextval('tags_id_seq'::regclass),
  tag_code character varying NOT NULL UNIQUE,
  tag_name_zh character varying NOT NULL,
  tag_name_en character varying,
  is_active boolean DEFAULT true,
  priority integer DEFAULT 100,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT tags_pkey PRIMARY KEY (id)
);
CREATE TABLE public.user_guidance_history (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  guidance_type text NOT NULL,
  guidance_data jsonb,
  focus_score numeric,
  clustering_method text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_guidance_history_pkey PRIMARY KEY (id),
  CONSTRAINT fk_user_guidance_history_user_id FOREIGN KEY (user_id) REFERENCES auth.users(id)
);