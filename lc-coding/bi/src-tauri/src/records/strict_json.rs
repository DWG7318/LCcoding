use std::cell::Cell;
use std::collections::HashSet;
use std::fmt;

use serde::de::{self, DeserializeOwned, DeserializeSeed, MapAccess, SeqAccess, Visitor};
use serde_json::{Map, Number, Value};

use super::RecordError;

const MAX_DEPTH: usize = 32;
const MAX_VALUES: usize = 16_384;
const MAX_OBJECT_MEMBERS: usize = 128;
const MAX_ARRAY_ITEMS: usize = 2_048;
const MAX_STRING_BYTES: usize = 4_096;

struct Seed<'a> {
    count: &'a Cell<usize>,
    depth: usize,
}

impl Seed<'_> {
    fn bump<E: de::Error>(&self) -> Result<(), E> {
        let next = self.count.get().saturating_add(1);
        if next > MAX_VALUES || self.depth > MAX_DEPTH {
            return Err(E::custom("resource limit"));
        }
        self.count.set(next);
        Ok(())
    }
}

impl<'de> DeserializeSeed<'de> for Seed<'_> {
    type Value = Value;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        self.bump()?;
        deserializer.deserialize_any(StrictVisitor {
            count: self.count,
            depth: self.depth,
        })
    }
}

struct StrictVisitor<'a> {
    count: &'a Cell<usize>,
    depth: usize,
}

impl<'de> Visitor<'de> for StrictVisitor<'_> {
    type Value = Value;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("bounded JSON")
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(Value::Null)
    }

    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Ok(Value::Null)
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
        Ok(Value::Bool(value))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E> {
        Ok(Value::Number(Number::from(value)))
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E> {
        Ok(Value::Number(Number::from(value)))
    }

    fn visit_f64<E: de::Error>(self, value: f64) -> Result<Self::Value, E> {
        Number::from_f64(value)
            .map(Value::Number)
            .ok_or_else(|| E::custom("non-finite number"))
    }

    fn visit_str<E: de::Error>(self, value: &str) -> Result<Self::Value, E> {
        if value.len() > MAX_STRING_BYTES {
            return Err(E::custom("string limit"));
        }
        Ok(Value::String(value.to_owned()))
    }

    fn visit_string<E: de::Error>(self, value: String) -> Result<Self::Value, E> {
        self.visit_str(&value)
    }

    fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element_seed(Seed {
            count: self.count,
            depth: self.depth + 1,
        })? {
            if values.len() == MAX_ARRAY_ITEMS {
                return Err(de::Error::custom("array limit"));
            }
            values.push(value);
        }
        Ok(Value::Array(values))
    }

    fn visit_map<A>(self, mut object: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut values = Map::new();
        let mut keys = HashSet::new();
        while let Some(key) = object.next_key::<String>()? {
            if key.len() > MAX_STRING_BYTES || !keys.insert(key.clone()) {
                return Err(de::Error::custom("invalid object key"));
            }
            if values.len() == MAX_OBJECT_MEMBERS {
                return Err(de::Error::custom("object limit"));
            }
            let key_count = self.count.get().saturating_add(1);
            if key_count > MAX_VALUES {
                return Err(de::Error::custom("value limit"));
            }
            self.count.set(key_count);
            let value = object.next_value_seed(Seed {
                count: self.count,
                depth: self.depth + 1,
            })?;
            values.insert(key, value);
        }
        Ok(Value::Object(values))
    }
}

pub fn parse<T: DeserializeOwned>(text: &str) -> Result<T, RecordError> {
    let count = Cell::new(0);
    let mut deserializer = serde_json::Deserializer::from_str(text);
    let value = Seed {
        count: &count,
        depth: 0,
    }
    .deserialize(&mut deserializer)
    .map_err(|_| RecordError::Invalid)?;
    deserializer.end().map_err(|_| RecordError::Invalid)?;
    serde_json::from_value(value).map_err(|_| RecordError::Invalid)
}
