import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
export const Root = () => (
  <Composition id="Asteroids" component={Film} durationInFrames={3135} fps={30} width={1920} height={1080} />
);
